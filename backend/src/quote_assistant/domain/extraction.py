from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from quote_assistant.domain.quality import QualityGrade


class FieldCategory(StrEnum):
    TITLE_BLOCK = "标题栏"
    CRITICAL_DIMENSION = "关键尺寸"
    TECHNICAL_REQUIREMENT = "技术要求"


@dataclass(frozen=True)
class ExtractedField:
    key: str
    label: str
    value: str | None
    category: FieldCategory


@dataclass(frozen=True)
class ExtractionRequest:
    """Input to the 提取引擎 Port: one image / PDF page plus 零件族标识."""

    page_content: bytes
    media_type: str
    part_family_id: str | None
    input_drawing_id: str


@dataclass(frozen=True)
class ExtractionResult:
    """Structured 读图取数 output plus the 图纸质量分级 signal."""

    quality_grade: QualityGrade
    is_assembly_or_exploded: bool
    fields: tuple[ExtractedField, ...]
