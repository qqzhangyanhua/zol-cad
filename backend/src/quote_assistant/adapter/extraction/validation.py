from __future__ import annotations

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

_CATEGORIES = Literal["标题栏", "关键尺寸", "技术要求"]


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


def parse_engine_result(raw: object) -> ExtractionResult:
    """Strict adapter-boundary validation. Failures never become domain objects."""
    try:
        payload = EngineResultPayload.model_validate(raw)
    except ValidationError as exc:
        raise ExtractionValidationFailed(
            "提取引擎返回结果未通过适配器校验，脏数据未进入领域层"
        ) from exc
    return payload.to_domain()
