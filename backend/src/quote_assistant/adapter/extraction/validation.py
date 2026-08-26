from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from quote_assistant.domain.errors import ExtractionValidationFailed
from quote_assistant.domain.extraction import (
    CANONICAL_FIELD_BY_KEY,
    ExtractedField,
    ExtractionResult,
    FieldCategory,
)
from quote_assistant.domain.quality import QualityGrade

LOGGER = logging.getLogger("quote_assistant.extraction.validation")

ADAPTER_VALIDATION_FAILED_REASON = "提取引擎返回结果未通过适配器校验，脏数据未进入领域层"

_CATEGORIES = Literal["标题栏", "关键尺寸", "技术要求"]

_IMAGE_BEARING_KEY_MARKERS = ("image", "base64", "page_content", "bytes")


class EngineFieldPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    value: str | None = None
    category: _CATEGORIES

    @field_validator("value")
    @classmethod
    def blank_value_is_missing(cls, value: str | None) -> str | None:
        if value == "":
            return None
        return value

    @model_validator(mode="after")
    def must_match_canonical_catalog(self) -> EngineFieldPayload:
        spec = CANONICAL_FIELD_BY_KEY.get(self.key)
        if spec is None:
            raise ValueError(f"未知提取字段: {self.key}")
        if self.label != spec.label:
            raise ValueError(f"字段「{self.key}」的标签必须是「{spec.label}」")
        if self.category != spec.category.value:
            raise ValueError(f"字段「{self.key}」的类别必须是「{spec.category.value}」")
        return self


class EngineResultPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quality_grade: QualityGrade
    is_assembly_or_exploded: bool
    fields: list[EngineFieldPayload] = Field(default_factory=list)

    @model_validator(mode="after")
    def keys_must_be_unique(self) -> EngineResultPayload:
        keys = [field.key for field in self.fields]
        if len(keys) != len(set(keys)):
            raise ValueError("提取字段 key 不能重复")
        return self

    def to_domain(self) -> ExtractionResult:
        return ExtractionResult(
            quality_grade=self.quality_grade,
            is_assembly_or_exploded=self.is_assembly_or_exploded,
            fields=tuple(
                ExtractedField(
                    key=field.key,
                    label=field.label,
                    value=field.value,
                    category=FieldCategory(field.category),
                )
                for field in self.fields
            ),
        )


def _looks_like_image_key(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in _IMAGE_BEARING_KEY_MARKERS)


def _short_scalar(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, bytes):
        return f"bytes(len={len(value)})"
    if isinstance(value, str):
        if len(value) <= 16:
            return repr(value)
        return f"str(len={len(value)})"
    if isinstance(value, (int, float)):
        return type(value).__name__
    return type(value).__name__


def _summarize_fields(fields: object) -> str:
    if not isinstance(fields, list):
        return f"type={type(fields).__name__}"
    items: list[str] = []
    for index, field in enumerate(fields[:24]):
        if not isinstance(field, dict):
            items.append(f"{index}:{type(field).__name__}")
            continue
        extras = [str(name) for name in field if name not in {"key", "label", "value", "category"}]
        value = field.get("value")
        bits = [
            f"key={_short_scalar(field.get('key'))}",
            f"value_type={'null' if value is None else type(value).__name__}",
        ]
        if extras:
            bits.append(f"extra={extras}")
        items.append(f"{index}({','.join(bits)})")
    suffix = f" +{len(fields) - 24}" if len(fields) > 24 else ""
    return f"len={len(fields)} [{'; '.join(items)}{suffix}]"


def summarize_engine_payload(raw: object) -> str:
    """Structure summary of a raw engine return. Never includes image bytes or long values."""
    if isinstance(raw, bytes):
        return f"type=bytes len={len(raw)}"
    if isinstance(raw, str):
        stripped = raw.lstrip()
        return f"type=str len={len(raw)} starts_with_object={stripped.startswith('{')}"
    if not isinstance(raw, dict):
        return f"type={type(raw).__name__}"

    keys = [str(key) for key in raw]
    parts = [f"keys={keys}"]
    for name in ("quality_grade", "is_assembly_or_exploded"):
        if name in raw:
            parts.append(f"{name}={_short_scalar(raw[name])}")
    if "fields" in raw:
        parts.append(f"fields={_summarize_fields(raw['fields'])}")
    extra = [
        key for key in keys if key not in {"quality_grade", "is_assembly_or_exploded", "fields"}
    ]
    if extra:
        parts.append(f"extra_keys={extra}")
        omitted = [key for key in extra if _looks_like_image_key(key)]
        if omitted:
            parts.append(f"omitted_image_keys={omitted}")
    return " ".join(parts)


def _validation_diagnostic(raw: object, exc: ValidationError) -> str:
    error_bits = [
        f"{'.'.join(str(part) for part in err.get('loc', ()))}:{err.get('type')}"
        for err in exc.errors()
    ]
    return (
        f"summary={summarize_engine_payload(raw)} "
        f"error_count={exc.error_count()} "
        f"errors=[{', '.join(error_bits)}]"
    )


def _emit_validation_diagnostic(diagnostic: str) -> None:
    # Alembic's fileConfig(disable_existing_loggers=True) can mute this logger
    # after import. Ticket 27 owns logging config; keep the line locatable.
    LOGGER.disabled = False
    LOGGER.propagate = True
    LOGGER.warning("engine_payload_validation_failed %s", diagnostic)


def parse_engine_result(raw: object) -> ExtractionResult:
    """Strict adapter-boundary validation. Failures never become domain objects."""
    try:
        payload = EngineResultPayload.model_validate(raw)
    except ValidationError as exc:
        diagnostic = _validation_diagnostic(raw, exc)
        _emit_validation_diagnostic(diagnostic)
        raise ExtractionValidationFailed(
            ADAPTER_VALIDATION_FAILED_REASON,
            diagnostic=diagnostic,
        ) from exc
    return payload.to_domain()
