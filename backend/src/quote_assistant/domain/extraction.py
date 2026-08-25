from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from quote_assistant.domain.quality import QualityGrade

LOOK_AT_DRAWING_DISCLAIMER = "本工具不替代看图，请重点复核公差密集区与技术要求"


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
class FieldSpec:
    key: str
    label: str
    category: FieldCategory


# Fixed form slots. Missing values stay empty — emptiness is a trust signal.
CANONICAL_FIELD_SPECS: tuple[FieldSpec, ...] = (
    FieldSpec("drawing_no", "图号", FieldCategory.TITLE_BLOCK),
    FieldSpec("part_name", "零件名称", FieldCategory.TITLE_BLOCK),
    FieldSpec("material", "材料", FieldCategory.TITLE_BLOCK),
    FieldSpec("quantity", "数量", FieldCategory.TITLE_BLOCK),
    FieldSpec("tightest_tolerance", "最严公差", FieldCategory.CRITICAL_DIMENSION),
    FieldSpec("max_envelope", "最大外形", FieldCategory.CRITICAL_DIMENSION),
    FieldSpec("deepest_hole", "最深孔", FieldCategory.CRITICAL_DIMENSION),
    FieldSpec("thinnest_wall", "最薄壁", FieldCategory.CRITICAL_DIMENSION),
    FieldSpec("heat_treatment", "热处理", FieldCategory.TECHNICAL_REQUIREMENT),
    FieldSpec("surface_treatment", "表面处理", FieldCategory.TECHNICAL_REQUIREMENT),
    FieldSpec("roughness", "粗糙度", FieldCategory.TECHNICAL_REQUIREMENT),
)

CANONICAL_FIELD_BY_KEY: dict[str, FieldSpec] = {spec.key: spec for spec in CANONICAL_FIELD_SPECS}


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


def empty_extraction_fields() -> tuple[ExtractedField, ...]:
    return tuple(
        ExtractedField(spec.key, spec.label, None, spec.category) for spec in CANONICAL_FIELD_SPECS
    )


def merge_extracted_fields(engine_fields: tuple[ExtractedField, ...]) -> tuple[ExtractedField, ...]:
    """Project engine output onto the canonical form. Omitted slots stay empty."""
    by_key = {field.key: field for field in engine_fields}
    merged: list[ExtractedField] = []
    for spec in CANONICAL_FIELD_SPECS:
        found = by_key.get(spec.key)
        value = found.value if found is not None else None
        if value == "":
            value = None
        merged.append(ExtractedField(spec.key, spec.label, value, spec.category))
    return tuple(merged)
