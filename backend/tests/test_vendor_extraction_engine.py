from __future__ import annotations

import logging

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, login
from quote_assistant.adapter.extraction.cost import InMemoryExtractionCostCounter
from quote_assistant.adapter.extraction.factory import build_extraction_engine
from quote_assistant.adapter.extraction.fake import FixtureExtractionEngine
from quote_assistant.adapter.extraction.fixtures import DIRTY_ENGINE_PAYLOAD, raw_fixture_for
from quote_assistant.adapter.extraction.vendor import (
    RATE_LIMITED_REASON,
    TIMEOUT_REASON,
    TRANSPORT_FAILED_REASON,
    VENDOR_NOT_CONFIGURED_REASON,
    UnconfiguredVendorTransport,
    VendorCompletionRequest,
    VendorCompletionResult,
    VendorExtractionEngine,
    VendorRateLimited,
    VendorTimeout,
    VendorTransportError,
)
from quote_assistant.config import Settings
from quote_assistant.domain.errors import (
    ExtractionRateLimited,
    ExtractionTimeout,
    ExtractionTransportFailed,
    ExtractionValidationFailed,
    ExtractionVendorNotConfigured,
)
from quote_assistant.domain.extraction import ExtractionRequest
from quote_assistant.domain.part_family import TARGET_PART_FAMILY_ID


def _request(content: bytes = PNG_1X1, drawing_id: str = "FX-TQ-01.png") -> ExtractionRequest:
    return ExtractionRequest(
        page_content=content,
        media_type="image/png",
        part_family_id=TARGET_PART_FAMILY_ID,
        input_drawing_id=drawing_id,
    )


class _PayloadTransport:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.last_request: VendorCompletionRequest | None = None

    def complete(self, request: VendorCompletionRequest) -> VendorCompletionResult:
        self.last_request = request
        return VendorCompletionResult(raw_payload=self.payload, prompt_tokens=12, estimated_cost=None)


class _RaiseTransport:
    def __init__(self, exc: Exception) -> None:
        self.exc = exc

    def complete(self, request: VendorCompletionRequest) -> VendorCompletionResult:
        del request
        raise self.exc


def test_工厂默认仍是假引擎() -> None:
    engine = build_extraction_engine(Settings(extraction_engine="fixture"))
    assert isinstance(engine, FixtureExtractionEngine)
    vendor = build_extraction_engine(Settings(extraction_engine="vendor"))
    assert isinstance(vendor, VendorExtractionEngine)


def test_未选定供应商的骨架拒绝调用付费API() -> None:
    recorder = InMemoryExtractionCostCounter()
    engine = VendorExtractionEngine(
        transport=UnconfiguredVendorTransport(),
        cost_recorder=recorder,
    )
    try:
        engine.extract(_request())
    except ExtractionVendorNotConfigured as exc:
        assert str(exc) == VENDOR_NOT_CONFIGURED_REASON
    else:
        raise AssertionError("应拒绝未选定供应商的调用")
    assert recorder.total_calls == 1
    assert recorder.events[0].outcome == "vendor_not_configured"
    assert recorder.events[0].estimated_cost is None
    assert recorder.events[0].page_byte_size == len(PNG_1X1)


def test_骨架校验失败按提取失败且脏数据不进领域() -> None:
    engine = VendorExtractionEngine(transport=_PayloadTransport(DIRTY_ENGINE_PAYLOAD))
    try:
        engine.extract(_request())
    except ExtractionValidationFailed:
        return
    raise AssertionError("脏载荷应被适配器拒绝")


def test_骨架校验通过后得到领域对象() -> None:
    engine = VendorExtractionEngine(transport=_PayloadTransport(raw_fixture_for("FX-TQ-01.png")))
    result = engine.extract(_request())
    assert result.fields[0].value == "FL-001"


def test_超时限流与传输失败映射为明确失败() -> None:
    timeout = VendorExtractionEngine(transport=_RaiseTransport(VendorTimeout("deadline")))
    try:
        timeout.extract(_request())
    except ExtractionTimeout as exc:
        assert str(exc) == TIMEOUT_REASON
    else:
        raise AssertionError("超时应映射为 ExtractionTimeout")

    limited = VendorExtractionEngine(transport=_RaiseTransport(VendorRateLimited("429")))
    try:
        limited.extract(_request())
    except ExtractionRateLimited as exc:
        assert str(exc) == RATE_LIMITED_REASON
    else:
        raise AssertionError("限流应映射为 ExtractionRateLimited")

    transport = VendorExtractionEngine(transport=_RaiseTransport(VendorTransportError("reset")))
    try:
        transport.extract(_request())
    except ExtractionTransportFailed as exc:
        assert str(exc) == TRANSPORT_FAILED_REASON
    else:
        raise AssertionError("传输失败应映射为 ExtractionTransportFailed")


def test_调用日志不落图像内容(caplog) -> None:
    marker = b"UNIQUE-IMAGE-BYTES-SHOULD-NOT-BE-LOGGED"
    content = PNG_1X1 + marker
    recorder = InMemoryExtractionCostCounter()
    logger = logging.getLogger("quote_assistant.extraction.vendor.test")
    engine = VendorExtractionEngine(
        transport=_PayloadTransport(raw_fixture_for("FX-TQ-01.png")),
        cost_recorder=recorder,
        logger=logger,
    )
    with caplog.at_level(logging.INFO, logger=logger.name):
        engine.extract(_request(content=content))
    blob = "\n".join(record.getMessage() for record in caplog.records)
    assert "UNIQUE-IMAGE-BYTES-SHOULD-NOT-BE-LOGGED" not in blob
    assert str(marker) not in blob
    assert "input_drawing_id=FX-TQ-01.png" in blob
    assert f"page_byte_size={len(content)}" in blob
    assert recorder.total_calls == 1
    assert recorder.events[0].outcome == "ok"
    assert recorder.events[0].estimated_cost is None


def test_超时失败有明确原因且可走现有重试(
    app, client: TestClient, db_session: Session
) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200

    app.state.extraction_engine = VendorExtractionEngine(
        transport=_RaiseTransport(VendorTimeout("deadline"))
    )
    uploaded = client.post(
        "/part-drawings",
        files=[("files", ("FX-TQ-01.png", PNG_1X1, "image/png"))],
    )
    assert uploaded.status_code == 200
    item = uploaded.json()["items"][0]
    assert item["status"] == "提取失败"
    assert item["extraction_failure_reason"] == TIMEOUT_REASON

    app.state.extraction_engine = FixtureExtractionEngine()
    retried = client.post(f"/part-drawings/{item['id']}/extract")
    assert retried.status_code == 200
    assert retried.json()["status"] == "已提取"


def test_骨架失败进入提取失败且可重试回假引擎(
    app, client: TestClient, db_session: Session
) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200

    app.state.extraction_engine = VendorExtractionEngine()
    uploaded = client.post(
        "/part-drawings",
        files=[("files", ("FX-TQ-01.png", PNG_1X1, "image/png"))],
    )
    assert uploaded.status_code == 200
    item = uploaded.json()["items"][0]
    assert item["status"] == "提取失败"
    assert item["extraction_failure_reason"] == VENDOR_NOT_CONFIGURED_REASON
    assert all(field["value"] is None for field in item["extracted_fields"])

    app.state.extraction_engine = FixtureExtractionEngine()
    retried = client.post(f"/part-drawings/{item['id']}/extract")
    assert retried.status_code == 200
    body = retried.json()
    assert body["status"] == "已提取"
    assert body["extraction_failure_reason"] is None
    fields = {field["key"]: field["value"] for field in body["extracted_fields"]}
    assert fields["drawing_no"] == "FL-001"
