from __future__ import annotations

from quote_assistant.domain.quality import QualityGrade

# Fixture keys follow `.scratch/mvp-quote-assistant/research/01-target-part-family/05-fixture-atlas.md`.
# Real sample images are still blocked; these raw presets drive the fake engine and seam-1 tests.
# Values that are not on the drawing stay None — do not invent a plausible number.

_TITLE = "标题栏"
_DIM = "关键尺寸"
_TECH = "技术要求"


def _field(key: str, label: str, value: str | None, category: str) -> dict[str, str | None]:
    return {"key": key, "label": label, "value": value, "category": category}


_CLEAR_FIELDS = [
    _field("drawing_no", "图号", "FL-001", _TITLE),
    _field("part_name", "零件名称", "法兰", _TITLE),
    _field("material", "材料", "45#", _TITLE),
    _field("quantity", "数量", "2", _TITLE),
    _field("tightest_tolerance", "最严公差", "IT7", _DIM),
    _field("max_envelope", "最大外形", "Ø120", _DIM),
    _field("deepest_hole", "最深孔", None, _DIM),
    _field("thinnest_wall", "最薄壁", None, _DIM),
    _field("heat_treatment", "热处理", None, _TECH),
    _field("surface_treatment", "表面处理", None, _TECH),
    _field("roughness", "粗糙度", "Ra3.2", _TECH),
]

_AVERAGE_FIELDS = [
    _field("drawing_no", "图号", "XT-018", _TITLE),
    _field("part_name", "零件名称", "轴套", _TITLE),
    _field("material", "材料", None, _TITLE),
    _field("quantity", "数量", "1", _TITLE),
    _field("tightest_tolerance", "最严公差", "IT8", _DIM),
    _field("max_envelope", "最大外形", "Ø45×80", _DIM),
    _field("deepest_hole", "最深孔", "Ø8×40", _DIM),
    _field("thinnest_wall", "最薄壁", None, _DIM),
    _field("heat_treatment", "热处理", None, _TECH),
    _field("surface_treatment", "表面处理", "发黑", _TECH),
    _field("roughness", "粗糙度", None, _TECH),
]

# Wiring fixture for seam-1 risk-label path. Not a ticket-01 factory sample.
_RISK_WIRE_FIELDS = [
    _field("drawing_no", "图号", "RL-WIRE-01", _TITLE),
    _field("part_name", "零件名称", "风险接线件", _TITLE),
    _field("material", "材料", "45#", _TITLE),
    _field("quantity", "数量", "1", _TITLE),
    _field("tightest_tolerance", "最严公差", "IT6", _DIM),
    _field("max_envelope", "最大外形", "Ø10×120", _DIM),
    _field("deepest_hole", "最深孔", "Ø8×48", _DIM),
    _field("thinnest_wall", "最薄壁", "1.5", _DIM),
    _field("heat_treatment", "热处理", None, _TECH),
    _field("surface_treatment", "表面处理", None, _TECH),
    _field("roughness", "粗糙度", None, _TECH),
]


RAW_FIXTURE_RESULTS: dict[str, dict[str, object]] = {
    "FX-TQ-01": {
        "quality_grade": QualityGrade.CLEAR.value,
        "is_assembly_or_exploded": False,
        "fields": _CLEAR_FIELDS,
    },
    "FX-TA-01": {
        "quality_grade": QualityGrade.AVERAGE.value,
        "is_assembly_or_exploded": False,
        "fields": _AVERAGE_FIELDS,
    },
    "FX-TP-01": {
        "quality_grade": QualityGrade.POOR.value,
        "is_assembly_or_exploded": False,
        "fields": [],
    },
    "FX-NQ-01": {
        "quality_grade": QualityGrade.CLEAR.value,
        "is_assembly_or_exploded": False,
        "fields": _CLEAR_FIELDS,
    },
    "FX-NA-01": {
        "quality_grade": QualityGrade.AVERAGE.value,
        "is_assembly_or_exploded": False,
        "fields": _AVERAGE_FIELDS,
    },
    "FX-NP-01": {
        "quality_grade": QualityGrade.POOR.value,
        "is_assembly_or_exploded": False,
        "fields": [],
    },
    "FX-ASM-01": {
        "quality_grade": QualityGrade.CLEAR.value,
        "is_assembly_or_exploded": True,
        "fields": [],
    },
    "DEFAULT": {
        "quality_grade": QualityGrade.CLEAR.value,
        "is_assembly_or_exploded": False,
        "fields": [],
    },
    "WIRE-RL-01": {
        "quality_grade": QualityGrade.CLEAR.value,
        "is_assembly_or_exploded": False,
        "fields": _RISK_WIRE_FIELDS,
    },
}

DIRTY_ENGINE_PAYLOAD: dict[str, object] = {
    "quality_grade": QualityGrade.CLEAR.value,
    "is_assembly_or_exploded": False,
    "fields": [
        {
            "key": "drawing_no",
            "label": "图号",
            "value": 12345,
            "category": "标题栏",
            "invented_confidence": 0.99,
        }
    ],
}


def resolve_fixture_key(input_drawing_id: str) -> str:
    """Match the longest known fixture key contained in the input-drawing id."""
    known = [key for key in RAW_FIXTURE_RESULTS if key != "DEFAULT"]
    for key in sorted(known, key=len, reverse=True):
        if key in input_drawing_id:
            return key
    return "DEFAULT"


def raw_fixture_for(input_drawing_id: str) -> dict[str, object]:
    return RAW_FIXTURE_RESULTS[resolve_fixture_key(input_drawing_id)]
