from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from quote_assistant.domain.entities import PartDrawing, PartDrawingStatus
from quote_assistant.domain.errors import (
    ExtractedFieldNotFound,
    IllegalPartDrawingTransition,
    IncompleteReview,
)
from quote_assistant.domain.extraction import (
    ADDED_KEY_SEPARATOR,
    CANONICAL_FIELD_BY_KEY,
    ExtractedField,
    FieldCategory,
    FieldSource,
    reviewable_fields,
    role_key_for_field,
)
from quote_assistant.domain.part_drawing_state import PartDrawingEvent, record_transition
from quote_assistant.domain.quality import QualityGrade


class FieldRiskClass(StrEnum):
    """Field-type class used by the high-risk confirmation table. Not model output."""

    DIMENSION = "尺寸类"
    TOLERANCE = "公差类"
    LOW_RISK = "低风险"


HIGH_RISK_FIELD_CLASSES: frozenset[FieldRiskClass] = frozenset(
    {FieldRiskClass.DIMENSION, FieldRiskClass.TOLERANCE}
)

# Domain-layer static constant. Grade never changes a high-risk class.
FIELD_RISK_CLASS_BY_KEY: dict[str, FieldRiskClass] = {
    "drawing_no": FieldRiskClass.LOW_RISK,
    "part_name": FieldRiskClass.LOW_RISK,
    "material": FieldRiskClass.LOW_RISK,
    "quantity": FieldRiskClass.LOW_RISK,
    "tightest_tolerance": FieldRiskClass.TOLERANCE,
    "max_envelope": FieldRiskClass.DIMENSION,
    "deepest_hole": FieldRiskClass.DIMENSION,
    "thinnest_wall": FieldRiskClass.DIMENSION,
    "heat_treatment": FieldRiskClass.LOW_RISK,
    "surface_treatment": FieldRiskClass.LOW_RISK,
    "roughness": FieldRiskClass.LOW_RISK,
}

REVIEWABLE_STATUSES: frozenset[PartDrawingStatus] = frozenset(
    {PartDrawingStatus.EXTRACTED, PartDrawingStatus.REVIEWING}
)

CRITICAL_DIMENSION_KINDS: frozenset[str] = frozenset(
    {
        "tightest_tolerance",
        "max_envelope",
        "deepest_hole",
        "thinnest_wall",
    }
)


@dataclass(frozen=True)
class ReviewFieldView:
    """Presentation of one extracted field after the backend applies the confirmation rule."""

    key: str
    label: str
    value: str | None
    category: FieldCategory
    requires_confirmation: bool
    confirmed: bool
    ignored: bool
    source: FieldSource


def field_risk_class(field_key: str) -> FieldRiskClass:
    role = role_key_for_field(field_key)
    return FIELD_RISK_CLASS_BY_KEY.get(role, FieldRiskClass.DIMENSION)


def field_requires_confirmation(field_key: str, quality_grade: QualityGrade | None) -> bool:
    """High-risk types always 需确认. Grade only affects low-risk fields."""
    if field_risk_class(field_key) in HIGH_RISK_FIELD_CLASSES:
        return True
    return quality_grade is not QualityGrade.CLEAR


def review_fields_for(drawing: PartDrawing) -> tuple[ReviewFieldView, ...]:
    return tuple(
        ReviewFieldView(
            key=field.key,
            label=field.label,
            value=field.value,
            category=field.category,
            requires_confirmation=field_requires_confirmation(field.key, drawing.quality_grade),
            confirmed=field.confirmed,
            ignored=field.ignored,
            source=field.source,
        )
        for field in reviewable_fields(drawing.extracted_fields)
    )


def unfinished_confirmation_items(drawing: PartDrawing) -> tuple[ReviewFieldView, ...]:
    return tuple(
        field
        for field in review_fields_for(drawing)
        if field.requires_confirmation and not field.confirmed and not field.ignored
    )


def fields_for_risk_labels(drawing: PartDrawing) -> tuple[ExtractedField, ...]:
    """Confirmed / current values that drive 风险标签. Ignored items do not participate."""
    return tuple(
        field for field in reviewable_fields(drawing.extracted_fields) if not field.ignored
    )


def incomplete_review_message(unfinished: tuple[ReviewFieldView, ...]) -> str:
    labels = "、".join(field.label for field in unfinished)
    return f"还不能标记已复核，仍有需确认项未处理：{labels}"


_UNCHANGED = object()


def _require_known_field(field_key: str, drawing: PartDrawing) -> None:
    known = {field.key for field in reviewable_fields(drawing.extracted_fields)}
    if field_key not in known:
        raise ExtractedFieldNotFound(f"提取字段不存在：{field_key}")


def require_review_editable(drawing: PartDrawing) -> None:
    if drawing.status is PartDrawingStatus.REVIEWED:
        raise IllegalPartDrawingTransition("零件图已复核，请先重新打开再修改")
    if drawing.status not in REVIEWABLE_STATUSES:
        current = drawing.status.value
        raise IllegalPartDrawingTransition(f"零件图处于「{current}」，不能开始复核")


def _replace_field(
    drawing: PartDrawing,
    field_key: str,
    *,
    value: str | object | None,
    confirm: bool,
    ignored: bool | object = _UNCHANGED,
) -> PartDrawing:
    require_review_editable(drawing)
    _require_known_field(field_key, drawing)
    updated: list[ExtractedField] = []
    found = False
    for field in reviewable_fields(drawing.extracted_fields):
        if field.key != field_key:
            updated.append(field)
            continue
        found = True
        next_value: str | None
        if value is _UNCHANGED:
            next_value = field.value
        elif value == "" or value is None:
            next_value = None
        elif isinstance(value, str):
            next_value = value
        else:
            next_value = field.value
        next_ignored = field.ignored if ignored is _UNCHANGED else bool(ignored)
        if value is not _UNCHANGED:
            next_ignored = False
        updated.append(
            ExtractedField(
                key=field.key,
                label=field.label,
                value=next_value,
                category=field.category,
                confirmed=True if confirm else field.confirmed,
                ignored=next_ignored,
                source=field.source,
            )
        )
    if not found:
        raise ExtractedFieldNotFound(f"提取字段不存在：{field_key}")
    return replace(drawing, extracted_fields=tuple(updated))


def confirm_extracted_field(drawing: PartDrawing, field_key: str) -> PartDrawing:
    return _replace_field(drawing, field_key, value=_UNCHANGED, confirm=True)


def edit_extracted_field(drawing: PartDrawing, field_key: str, value: str | None) -> PartDrawing:
    return _replace_field(drawing, field_key, value=value, confirm=True)


def ignore_extracted_field(drawing: PartDrawing, field_key: str) -> PartDrawing:
    return _replace_field(drawing, field_key, value=_UNCHANGED, confirm=False, ignored=True)


def unignore_extracted_field(drawing: PartDrawing, field_key: str) -> PartDrawing:
    return _replace_field(drawing, field_key, value=_UNCHANGED, confirm=False, ignored=False)


def add_critical_dimension(
    drawing: PartDrawing,
    kind: str,
    value: str,
    label: str | None = None,
) -> PartDrawing:
    """补录一条 AI 未提出的关键尺寸。空槽写入原位；已有值则追加同等对待的补录项。"""
    require_review_editable(drawing)
    if kind not in CRITICAL_DIMENSION_KINDS:
        raise ExtractedFieldNotFound(f"不能补录该字段：{kind}")
    spec = CANONICAL_FIELD_BY_KEY[kind]
    cleaned = value.strip()
    if cleaned == "":
        raise ExtractedFieldNotFound("补录的关键尺寸不能为空")
    fields = list(reviewable_fields(drawing.extracted_fields))
    filled = False
    updated: list[ExtractedField] = []
    for field in fields:
        if field.key == kind and field.value is None:
            updated.append(
                ExtractedField(
                    key=field.key,
                    label=field.label,
                    value=cleaned,
                    category=field.category,
                    confirmed=True,
                    ignored=False,
                    source=FieldSource.ADDED,
                )
            )
            filled = True
        else:
            updated.append(field)
    if not filled:
        existing_added = [
            field for field in updated if field.key.startswith(f"{kind}{ADDED_KEY_SEPARATOR}")
        ]
        next_index = 1 + len(existing_added)
        extra_label = label.strip() if label and label.strip() else spec.label
        updated.append(
            ExtractedField(
                key=f"{kind}{ADDED_KEY_SEPARATOR}{next_index}",
                label=extra_label,
                value=cleaned,
                category=FieldCategory.CRITICAL_DIMENSION,
                confirmed=True,
                ignored=False,
                source=FieldSource.ADDED,
            )
        )
    return replace(drawing, extracted_fields=tuple(updated))


def begin_reviewing(
    drawing: PartDrawing,
    *,
    occurred_at: datetime,
    sequence_no: int,
    actor_user_id: UUID | None,
) -> tuple[PartDrawing, PartDrawingEvent | None]:
    if drawing.status is PartDrawingStatus.REVIEWING:
        return drawing, None
    if drawing.status is not PartDrawingStatus.EXTRACTED:
        current = drawing.status.value
        raise IllegalPartDrawingTransition(f"零件图处于「{current}」，不能开始复核")
    updated, event = record_transition(
        drawing,
        PartDrawingStatus.REVIEWING,
        occurred_at=occurred_at,
        sequence_no=sequence_no,
        actor_user_id=actor_user_id,
    )
    return updated, event


def complete_review(
    drawing: PartDrawing,
    *,
    occurred_at: datetime,
    sequence_no: int,
    actor_user_id: UUID | None,
) -> tuple[PartDrawing, PartDrawingEvent]:
    if drawing.status not in REVIEWABLE_STATUSES:
        raise IllegalPartDrawingTransition(f"零件图处于「{drawing.status.value}」，不能标记已复核")
    unfinished = unfinished_confirmation_items(drawing)
    if unfinished:
        raise IncompleteReview(incomplete_review_message(unfinished))
    return record_transition(
        drawing,
        PartDrawingStatus.REVIEWED,
        occurred_at=occurred_at,
        sequence_no=sequence_no,
        actor_user_id=actor_user_id,
    )


def reopen_review(
    drawing: PartDrawing,
    *,
    occurred_at: datetime,
    sequence_no: int,
    actor_user_id: UUID | None,
) -> tuple[PartDrawing, PartDrawingEvent]:
    if drawing.status is not PartDrawingStatus.REVIEWED:
        raise IllegalPartDrawingTransition(
            f"零件图处于「{drawing.status.value}」，不能重新打开复核"
        )
    return record_transition(
        drawing,
        PartDrawingStatus.REVIEWING,
        occurred_at=occurred_at,
        sequence_no=sequence_no,
        actor_user_id=actor_user_id,
    )
