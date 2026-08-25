from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from quote_assistant.domain.entities import PartDrawing, PartDrawingStatus
from quote_assistant.domain.errors import InvalidQuoteSheetTemplate
from quote_assistant.domain.extraction import reviewable_fields, role_key_for_field
from quote_assistant.domain.part_family import experimental_mark_for
from quote_assistant.domain.quality import LOW_QUALITY_MARK_TEXT
from quote_assistant.domain.review import fields_for_risk_labels
from quote_assistant.domain.risk_labels import evaluate_risk_labels

# Closed catalog of values a 报价底稿 column can pull. Team maps these onto
# a factory's existing sheet at onboarding. Not a user-facing mapping UI.
QUOTE_SHEET_SOURCE_KEYS: frozenset[str] = frozenset(
    {
        "drawing_no",
        "part_name",
        "material",
        "quantity",
        "tightest_tolerance",
        "max_envelope",
        "deepest_hole",
        "thinnest_wall",
        "heat_treatment",
        "surface_treatment",
        "roughness",
        "original_filename",
        "risk_labels",
        "experimental_mark",
        "low_quality_mark",
    }
)

RISK_LABELS_SOURCE_KEY = "risk_labels"
EXPERIMENTAL_MARK_SOURCE_KEY = "experimental_mark"
LOW_QUALITY_MARK_SOURCE_KEY = "low_quality_mark"

REQUIRED_QUOTE_SHEET_SOURCE_KEYS: tuple[str, ...] = (
    RISK_LABELS_SOURCE_KEY,
    EXPERIMENTAL_MARK_SOURCE_KEY,
    LOW_QUALITY_MARK_SOURCE_KEY,
)

DEFAULT_RISK_LABELS_HEADER = "风险标签"
DEFAULT_EXPERIMENTAL_MARK_HEADER = "实验性、不保证"
DEFAULT_LOW_QUALITY_MARK_HEADER = "低质量图，结果不可靠"

_REQUIRED_HEADER_BY_KEY: dict[str, str] = {
    RISK_LABELS_SOURCE_KEY: DEFAULT_RISK_LABELS_HEADER,
    EXPERIMENTAL_MARK_SOURCE_KEY: DEFAULT_EXPERIMENTAL_MARK_HEADER,
    LOW_QUALITY_MARK_SOURCE_KEY: DEFAULT_LOW_QUALITY_MARK_HEADER,
}


class QuoteSheetFileFormat(StrEnum):
    XLSX = "xlsx"
    CSV = "csv"


@dataclass(frozen=True)
class QuoteSheetColumn:
    source_key: str
    header: str


@dataclass(frozen=True)
class QuoteSheetTemplate:
    """One factory's 报价底稿 column template. Backend-maintained, not in 管理员 UI."""

    columns: tuple[QuoteSheetColumn, ...]


@dataclass(frozen=True)
class QuoteSheetTable:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class QuoteSheetFile:
    filename: str
    media_type: str
    content: bytes


def default_quote_sheet_template() -> QuoteSheetTemplate:
    """Typical factory sheet: 标题栏 + 关键尺寸 + 技术要求 + the three required marks."""
    return QuoteSheetTemplate(
        columns=(
            QuoteSheetColumn("drawing_no", "图号"),
            QuoteSheetColumn("part_name", "零件名称"),
            QuoteSheetColumn("material", "材料"),
            QuoteSheetColumn("quantity", "数量"),
            QuoteSheetColumn("tightest_tolerance", "最严公差"),
            QuoteSheetColumn("max_envelope", "最大外形"),
            QuoteSheetColumn("deepest_hole", "最深孔"),
            QuoteSheetColumn("thinnest_wall", "最薄壁"),
            QuoteSheetColumn("heat_treatment", "热处理"),
            QuoteSheetColumn("surface_treatment", "表面处理"),
            QuoteSheetColumn("roughness", "粗糙度"),
            QuoteSheetColumn(RISK_LABELS_SOURCE_KEY, DEFAULT_RISK_LABELS_HEADER),
            QuoteSheetColumn(EXPERIMENTAL_MARK_SOURCE_KEY, DEFAULT_EXPERIMENTAL_MARK_HEADER),
            QuoteSheetColumn(LOW_QUALITY_MARK_SOURCE_KEY, DEFAULT_LOW_QUALITY_MARK_HEADER),
        )
    )


def parse_quote_sheet_columns(raw: Sequence[object]) -> tuple[QuoteSheetColumn, ...]:
    parsed: list[QuoteSheetColumn] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise InvalidQuoteSheetTemplate("报价底稿模板列必须是对象")
        source_key = item.get("source_key")
        header = item.get("header")
        if not isinstance(source_key, str) or source_key not in QUOTE_SHEET_SOURCE_KEYS:
            raise InvalidQuoteSheetTemplate(f"报价底稿模板含有未知源字段：{source_key}")
        if not isinstance(header, str) or header.strip() == "":
            raise InvalidQuoteSheetTemplate("报价底稿模板列标题不能为空")
        if source_key in seen:
            raise InvalidQuoteSheetTemplate(f"报价底稿模板重复配置了源字段：{source_key}")
        seen.add(source_key)
        parsed.append(QuoteSheetColumn(source_key=source_key, header=header.strip()))
    return tuple(parsed)


def ensure_required_quote_sheet_columns(
    columns: Sequence[QuoteSheetColumn],
) -> tuple[QuoteSheetColumn, ...]:
    """Keep factory order/headers; append required marks if onboarding omitted them."""
    validated = parse_quote_sheet_columns(
        [{"source_key": column.source_key, "header": column.header} for column in columns]
    )
    existing = {column.source_key for column in validated}
    completed = list(validated)
    for source_key in REQUIRED_QUOTE_SHEET_SOURCE_KEYS:
        if source_key not in existing:
            completed.append(
                QuoteSheetColumn(source_key=source_key, header=_REQUIRED_HEADER_BY_KEY[source_key])
            )
    return tuple(completed)


def resolve_quote_sheet_template(stored: QuoteSheetTemplate | None) -> QuoteSheetTemplate:
    if stored is None or not stored.columns:
        return default_quote_sheet_template()
    return QuoteSheetTemplate(columns=ensure_required_quote_sheet_columns(stored.columns))


def unreviewed_drawings_for_export(drawings: Sequence[PartDrawing]) -> tuple[PartDrawing, ...]:
    return tuple(
        drawing for drawing in drawings if drawing.status is not PartDrawingStatus.REVIEWED
    )


def incomplete_export_message(drawings: Sequence[PartDrawing]) -> str:
    names = "、".join(drawing.original_filename for drawing in drawings)
    return f"报价任务中还有未完成复核的零件图：{names}"


def quote_sheet_filename(task_name: str, file_format: QuoteSheetFileFormat) -> str:
    cleaned = "".join("_" if char in '\\/:*?"<>|' else char for char in task_name.strip())
    cleaned = cleaned.strip(" .") or "报价任务"
    return f"{cleaned}-报价底稿.{file_format.value}"


def quote_sheet_media_type(file_format: QuoteSheetFileFormat) -> str:
    if file_format is QuoteSheetFileFormat.CSV:
        return "text/csv; charset=utf-8"
    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def build_quote_sheet_table(
    drawings: Sequence[PartDrawing],
    template: QuoteSheetTemplate,
) -> QuoteSheetTable:
    resolved = resolve_quote_sheet_template(template)
    headers = tuple(column.header for column in resolved.columns)
    rows = tuple(_row_for(drawing, resolved.columns) for drawing in drawings)
    return QuoteSheetTable(headers=headers, rows=rows)


def _row_for(drawing: PartDrawing, columns: Sequence[QuoteSheetColumn]) -> tuple[str, ...]:
    return tuple(_cell_for(drawing, column.source_key) for column in columns)


def _cell_for(drawing: PartDrawing, source_key: str) -> str:
    if source_key == RISK_LABELS_SOURCE_KEY:
        labels = evaluate_risk_labels(fields_for_risk_labels(drawing))
        return "、".join(label.name.value for label in labels)
    if source_key == EXPERIMENTAL_MARK_SOURCE_KEY:
        return experimental_mark_for(drawing.part_family_id) or ""
    if source_key == LOW_QUALITY_MARK_SOURCE_KEY:
        return LOW_QUALITY_MARK_TEXT if drawing.low_quality_unreliable else ""
    if source_key == "original_filename":
        return drawing.original_filename
    values: list[str] = []
    for field in reviewable_fields(drawing.extracted_fields):
        if field.ignored or not field.value:
            continue
        if role_key_for_field(field.key) == source_key:
            values.append(field.value)
    return "；".join(values)
