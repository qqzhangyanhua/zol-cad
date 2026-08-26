from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from dataclasses import dataclass
from typing import Protocol

from quote_assistant.adapter.extraction.cost import (
    ExtractionCostEvent,
    ExtractionCostRecorder,
    InMemoryExtractionCostCounter,
)
from quote_assistant.adapter.extraction.validation import parse_engine_result
from quote_assistant.domain.errors import (
    ExtractionRateLimited,
    ExtractionTimeout,
    ExtractionTransportFailed,
    ExtractionValidationFailed,
    ExtractionVendorNotConfigured,
)
from quote_assistant.domain.extraction import ExtractionRequest, ExtractionResult
from quote_assistant.domain.prompt_templates import prompt_template_for

LOGGER = logging.getLogger("quote_assistant.extraction.vendor")

VENDOR_NOT_CONFIGURED_REASON = (
    "真实提取引擎尚未选定供应商（票 02 / ADR-0009 仍为模板），未调用任何付费 API"
)
TIMEOUT_REASON = "读图取数超时，请重试"
RATE_LIMITED_REASON = "读图取数被限流，请稍后重试"
TRANSPORT_FAILED_REASON = "读图取数调用失败，请重试"


@dataclass(frozen=True)
class VendorCompletionRequest:
    """Payload handed to a future vendor transport. Logs must use metadata only."""

    input_drawing_id: str
    media_type: str
    part_family_id: str
    prompt_template_id: str
    page_byte_size: int
    page_content: bytes


@dataclass(frozen=True)
class VendorCompletionResult:
    raw_payload: object
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    estimated_cost: float | None = None


class VendorTimeout(Exception):
    """Transport-level timeout. Mapped to ExtractionTimeout."""


class VendorRateLimited(Exception):
    """Transport-level 429 / quota. Mapped to ExtractionRateLimited."""


class VendorTransportError(Exception):
    """Other transport / protocol failure. Mapped to ExtractionTransportFailed."""


class VendorTransport(Protocol):
    def complete(self, request: VendorCompletionRequest) -> VendorCompletionResult:
        """Call the selected vendor. Must not be implemented as a live paid API until ticket 02 closes."""


class UnconfiguredVendorTransport:
    """Default transport while ADR-0009 is a template. Refuses to call any paid API."""

    def complete(self, request: VendorCompletionRequest) -> VendorCompletionResult:
        del request
        raise ExtractionVendorNotConfigured(VENDOR_NOT_CONFIGURED_REASON)


def _log_extract(
    logger: logging.Logger,
    *,
    phase: str,
    input_drawing_id: str,
    media_type: str,
    page_byte_size: int,
    part_family_id: str,
    prompt_template_id: str,
    outcome: str | None = None,
) -> None:
    logger.info(
        "vendor_extract_%s input_drawing_id=%s media_type=%s page_byte_size=%s "
        "part_family_id=%s prompt_template_id=%s%s",
        phase,
        input_drawing_id,
        media_type,
        page_byte_size,
        part_family_id,
        prompt_template_id,
        f" outcome={outcome}" if outcome is not None else "",
    )


class VendorExtractionEngine:
    """Skeleton 提取引擎 behind the Port. Not the default. Does not call a live paid API."""

    def __init__(
        self,
        transport: VendorTransport | None = None,
        cost_recorder: ExtractionCostRecorder | None = None,
        logger: logging.Logger | None = None,
        timeout_seconds: float = 60,
        retry_count: int = 0,
    ) -> None:
        self._transport = transport or UnconfiguredVendorTransport()
        self._cost = cost_recorder or InMemoryExtractionCostCounter()
        self._log = logger or LOGGER
        self._timeout_seconds = timeout_seconds
        self._retry_count = max(0, retry_count)

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        template = prompt_template_for(request.part_family_id)
        page_byte_size = len(request.page_content)
        completion = VendorCompletionRequest(
            input_drawing_id=request.input_drawing_id,
            media_type=request.media_type,
            part_family_id=request.part_family_id,
            prompt_template_id=template.id,
            page_byte_size=page_byte_size,
            page_content=request.page_content,
        )
        _log_extract(
            self._log,
            phase="start",
            input_drawing_id=request.input_drawing_id,
            media_type=request.media_type,
            page_byte_size=page_byte_size,
            part_family_id=request.part_family_id,
            prompt_template_id=template.id,
        )
        outcome = "unknown"
        prompt_tokens: int | None = None
        completion_tokens: int | None = None
        estimated_cost: float | None = None
        try:
            completed = self._complete_with_retries(completion)
            prompt_tokens = completed.prompt_tokens
            completion_tokens = completed.completion_tokens
            estimated_cost = completed.estimated_cost
            parsed = parse_engine_result(completed.raw_payload)
            outcome = "ok"
            return parsed
        except ExtractionValidationFailed:
            outcome = "validation_failed"
            raise
        except ExtractionVendorNotConfigured:
            outcome = "vendor_not_configured"
            raise
        except VendorTimeout as exc:
            outcome = "timeout"
            raise ExtractionTimeout(TIMEOUT_REASON) from exc
        except VendorRateLimited as exc:
            outcome = "rate_limited"
            raise ExtractionRateLimited(RATE_LIMITED_REASON) from exc
        except VendorTransportError as exc:
            outcome = "transport_failed"
            raise ExtractionTransportFailed(TRANSPORT_FAILED_REASON) from exc
        finally:
            self._cost.record(
                ExtractionCostEvent(
                    input_drawing_id=request.input_drawing_id,
                    page_byte_size=page_byte_size,
                    prompt_template_id=template.id,
                    outcome=outcome,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    estimated_cost=estimated_cost,
                )
            )
            _log_extract(
                self._log,
                phase="finish",
                input_drawing_id=request.input_drawing_id,
                media_type=request.media_type,
                page_byte_size=page_byte_size,
                part_family_id=request.part_family_id,
                prompt_template_id=template.id,
                outcome=outcome,
            )

    def _complete_with_retries(self, request: VendorCompletionRequest) -> VendorCompletionResult:
        attempts = 1 + self._retry_count
        last_retryable: BaseException | None = None
        for attempt in range(attempts):
            try:
                return self._complete_once(request)
            except (VendorTimeout, VendorRateLimited, VendorTransportError) as exc:
                last_retryable = exc
                if attempt + 1 >= attempts:
                    raise
                self._log.info(
                    "vendor_extract_retry attempt=%s/%s input_drawing_id=%s error=%s",
                    attempt + 1,
                    attempts,
                    request.input_drawing_id,
                    type(exc).__name__,
                )
        assert last_retryable is not None
        raise last_retryable

    def _complete_once(self, request: VendorCompletionRequest) -> VendorCompletionResult:
        if self._timeout_seconds <= 0:
            return self._transport.complete(request)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self._transport.complete, request)
            try:
                return future.result(timeout=self._timeout_seconds)
            except FuturesTimeout as exc:
                raise VendorTimeout("deadline exceeded") from exc
