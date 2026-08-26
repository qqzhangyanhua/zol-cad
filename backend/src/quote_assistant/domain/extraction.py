from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from quote_assistant.domain.quality import QualityGrade

LOOK_AT_DRAWING_DISCLAIMER = "本工具不替代看图，请重点复核公差密集区与技术要求"


class FieldCategory(StrEnum):
    TITLE_BLOCK = "标题栏"
    CRITICAL_DIMENSION = "关键尺寸"
    TECHNICAL_REQUIREMENT = "技术要求"


class FieldSource(StrEnum):
    EXTRACTED = "extracted"
    ADDED = "added"


ADDED_KEY_SEPARATOR = "__added__"


@dataclass(frozen=True)
class ExtractedField:
    key: str
    label: str
    value: str | None
    category: FieldCategory
    confirmed: bool = False
    ignored: bool = False
    source: FieldSource = FieldSource.EXTRACTED


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
class RenderedPage:
    """The single page actually handed to the 提取引擎.

    多页 PDF 只处理报价员指定的那一页，所以引擎收到的必须是那一页渲染出来的图像，
    而不是整份原始文件。图片原样透传。
    """

    content: bytes
    media_type: str


@dataclass(frozen=True)
class ExtractionRequest:
    """Input to the 提取引擎 Port: one image / PDF page plus 零件族标识."""

    page_content: bytes
    media_type: str
    part_family_id: str
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


def role_key_for_field(field_key: str) -> str:
    """Map a补录 extra key (`tightest_tolerance__added__1`) back to its canonical role."""
    if ADDED_KEY_SEPARATOR in field_key:
        prefix, _sep, suffix = field_key.partition(ADDED_KEY_SEPARATOR)
        if prefix in CANONICAL_FIELD_BY_KEY and suffix.isdigit():
            return prefix
    return field_key


def is_added_field_key(field_key: str) -> bool:
    return role_key_for_field(field_key) != field_key


def merge_extracted_fields(engine_fields: tuple[ExtractedField, ...]) -> tuple[ExtractedField, ...]:
    """Project engine output onto the canonical form. Omitted slots stay empty."""
    by_key = {field.key: field for field in engine_fields}
    merged: list[ExtractedField] = []
    for spec in CANONICAL_FIELD_SPECS:
        found = by_key.get(spec.key)
        value = found.value if found is not None else None
        if value == "":
            value = None
        confirmed = found.confirmed if found is not None else False
        ignored = found.ignored if found is not None else False
        source = found.source if found is not None else FieldSource.EXTRACTED
        merged.append(
            ExtractedField(spec.key, spec.label, value, spec.category, confirmed, ignored, source)
        )
    return tuple(merged)


def reviewable_fields(stored: tuple[ExtractedField, ...]) -> tuple[ExtractedField, ...]:
    """Canonical slots plus 报价员补录的额外关键尺寸. Extras stay after the form slots."""
    extras = tuple(field for field in stored if field.key not in CANONICAL_FIELD_BY_KEY)
    return merge_extracted_fields(stored) + extras


def has_review_edit(field: ExtractedField) -> bool:
    """A field the 报价员 already touched — retry extract must keep it."""
    return field.confirmed or field.ignored or field.source is FieldSource.ADDED


def merge_extraction_preserving_review(
    existing: tuple[ExtractedField, ...],
    engine_fields: tuple[ExtractedField, ...],
) -> tuple[ExtractedField, ...]:
    """Apply a new extract without overwriting 复核 edits or 补录项."""
    incoming = merge_extracted_fields(engine_fields)
    existing_by_key = {field.key: field for field in existing}
    preserved: list[ExtractedField] = []
    for field in incoming:
        previous = existing_by_key.get(field.key)
        if previous is not None and has_review_edit(previous):
            preserved.append(previous)
        else:
            preserved.append(field)
    for field in existing:
        if field.key not in CANONICAL_FIELD_BY_KEY:
            preserved.append(field)
    return tuple(preserved)
