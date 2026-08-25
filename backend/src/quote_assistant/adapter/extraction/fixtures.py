from __future__ import annotations

from quote_assistant.domain.extraction import ExtractedField, ExtractionResult, FieldCategory
from quote_assistant.domain.quality import QualityGrade

# Fixture keys follow `.scratch/mvp-quote-assistant/research/01-target-part-family/05-fixture-atlas.md`.
# Real sample images are still blocked; these presets drive the fake engine and seam-1 tests.

_TITLE = FieldCategory.TITLE_BLOCK
_DIM = FieldCategory.CRITICAL_DIMENSION
_TECH = FieldCategory.TECHNICAL_REQUIREMENT

_CLEAR_FIELDS = (
    ExtractedField("drawing_no", "图号", "FL-001", _TITLE),
    ExtractedField("part_name", "零件名称", "法兰", _TITLE),
    ExtractedField("material", "材料", "45#", _TITLE),
    ExtractedField("quantity", "数量", "2", _TITLE),
    ExtractedField("tightest_tolerance", "最严公差", "IT7", _DIM),
    ExtractedField("max_envelope", "最大外形", "Ø120", _DIM),
    ExtractedField("heat_treatment", "热处理", None, _TECH),
)

_AVERAGE_FIELDS = (
    ExtractedField("drawing_no", "图号", "XT-018", _TITLE),
    ExtractedField("part_name", "零件名称", "轴套", _TITLE),
    ExtractedField("material", "材料", None, _TITLE),
    ExtractedField("quantity", "数量", "1", _TITLE),
    ExtractedField("tightest_tolerance", "最严公差", "IT8", _DIM),
    ExtractedField("max_envelope", "最大外形", "Ø45×80", _DIM),
    ExtractedField("surface_treatment", "表面处理", "发黑", _TECH),
)

FIXTURE_RESULTS: dict[str, ExtractionResult] = {
    "FX-TQ-01": ExtractionResult(
        quality_grade=QualityGrade.CLEAR,
        is_assembly_or_exploded=False,
        fields=_CLEAR_FIELDS,
    ),
    "FX-TA-01": ExtractionResult(
        quality_grade=QualityGrade.AVERAGE,
        is_assembly_or_exploded=False,
        fields=_AVERAGE_FIELDS,
    ),
    "FX-TP-01": ExtractionResult(
        quality_grade=QualityGrade.POOR,
        is_assembly_or_exploded=False,
        fields=(),
    ),
    "FX-NQ-01": ExtractionResult(
        quality_grade=QualityGrade.CLEAR,
        is_assembly_or_exploded=False,
        fields=_CLEAR_FIELDS,
    ),
    "FX-NA-01": ExtractionResult(
        quality_grade=QualityGrade.AVERAGE,
        is_assembly_or_exploded=False,
        fields=_AVERAGE_FIELDS,
    ),
    "FX-NP-01": ExtractionResult(
        quality_grade=QualityGrade.POOR,
        is_assembly_or_exploded=False,
        fields=(),
    ),
    "FX-ASM-01": ExtractionResult(
        quality_grade=QualityGrade.CLEAR,
        is_assembly_or_exploded=True,
        fields=(),
    ),
    "DEFAULT": ExtractionResult(
        quality_grade=QualityGrade.CLEAR,
        is_assembly_or_exploded=False,
        fields=(),
    ),
}


def resolve_fixture_key(input_drawing_id: str) -> str:
    """Match the longest known fixture key contained in the input-drawing id."""
    known = [key for key in FIXTURE_RESULTS if key != "DEFAULT"]
    for key in sorted(known, key=len, reverse=True):
        if key in input_drawing_id:
            return key
    return "DEFAULT"
