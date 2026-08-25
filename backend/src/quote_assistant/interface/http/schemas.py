from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from quote_assistant.domain.correction import CorrectionFieldTypeStat, CorrectionRecord
from quote_assistant.domain.entities import PartDrawing, PartDrawingStatus, Role
from quote_assistant.domain.extraction import (
    LOOK_AT_DRAWING_DISCLAIMER,
    FieldCategory,
    FieldSource,
)
from quote_assistant.domain.part_drawing_state import auto_prefill_allowed
from quote_assistant.domain.quality import (
    ASSEMBLY_OUT_OF_SCOPE_TEXT,
    LOW_QUALITY_MARK_TEXT,
    POOR_GRADE_ADVISE_TEXT,
    QUALITY_GRADE_DISCLAIMER,
    QualityGrade,
)
from quote_assistant.domain.review import (
    fields_for_risk_labels,
    review_fields_for,
    unfinished_confirmation_items,
)
from quote_assistant.domain.risk_labels import (
    NO_JUDGABLE_RISK_ITEMS_MESSAGE,
    RiskLabelName,
    evaluate_risk_labels,
)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class OkResponse(BaseModel):
    ok: bool = True


class CurrentUserResponse(BaseModel):
    username: str
    factory_name: str
    role: Role


class ExtractedFieldResponse(BaseModel):
    key: str
    label: str
    value: str | None
    category: FieldCategory
    requires_confirmation: bool
    confirmed: bool
    ignored: bool
    source: FieldSource


class UpdateExtractedFieldRequest(BaseModel):
    value: str | None = Field(default=None, max_length=200)


class AddCriticalDimensionRequest(BaseModel):
    kind: str = Field(min_length=1, max_length=80)
    value: str = Field(min_length=1, max_length=200)
    label: str | None = Field(default=None, max_length=80)


class RiskLabelResponse(BaseModel):
    name: RiskLabelName
    rule_id: str
    triggering_value: str
    reason: str


class PartDrawingResponse(BaseModel):
    id: UUID
    original_filename: str
    uploaded_at: datetime
    content_type: str
    byte_size: int
    page_count: int
    selected_page: int
    status: PartDrawingStatus
    quality_grade: QualityGrade | None
    is_assembly_or_exploded: bool
    low_quality_unreliable: bool
    auto_prefill_allowed: bool
    quality_grade_disclaimer: str
    advise_manual_message: str | None
    out_of_scope_message: str | None
    low_quality_mark: str | None
    extracted_fields: list[ExtractedFieldResponse]
    extraction_failure_reason: str | None
    look_at_drawing_disclaimer: str
    risk_labels: list[RiskLabelResponse]
    no_judgable_risk_message: str
    pending_confirmation_count: int
    pending_confirmation_labels: list[str]


class PartDrawingListResponse(BaseModel):
    items: list[PartDrawingResponse]


class RejectedUploadResponse(BaseModel):
    original_filename: str
    detail: str


class UploadPartDrawingsResponse(BaseModel):
    items: list[PartDrawingResponse]
    rejected: list[RejectedUploadResponse]


class OriginalAccessResponse(BaseModel):
    url: str
    expires_at: datetime
    content_type: str
    original_filename: str
    page_count: int
    selected_page: int


class PartDrawingEventResponse(BaseModel):
    id: UUID
    from_status: PartDrawingStatus | None
    to_status: PartDrawingStatus
    occurred_at: datetime
    sequence_no: int


class PartDrawingEventListResponse(BaseModel):
    items: list[PartDrawingEventResponse]


class CorrectionRecordResponse(BaseModel):
    id: UUID
    part_drawing_id: UUID
    field_key: str
    field_type: str
    old_value: str | None
    new_value: str | None
    actor_user_id: UUID
    occurred_at: datetime


class CorrectionRecordListResponse(BaseModel):
    items: list[CorrectionRecordResponse]


class CorrectionFieldTypeStatResponse(BaseModel):
    field_type: str
    correction_count: int


class CorrectionStatsResponse(BaseModel):
    items: list[CorrectionFieldTypeStatResponse]
    purpose: str


def to_correction_record_response(record: CorrectionRecord) -> CorrectionRecordResponse:
    return CorrectionRecordResponse(
        id=record.id,
        part_drawing_id=record.part_drawing_id,
        field_key=record.field_key,
        field_type=record.field_type,
        old_value=record.old_value,
        new_value=record.new_value,
        actor_user_id=record.actor_user_id,
        occurred_at=record.occurred_at,
    )


def to_correction_stat_response(stat: CorrectionFieldTypeStat) -> CorrectionFieldTypeStatResponse:
    return CorrectionFieldTypeStatResponse(
        field_type=stat.field_type,
        correction_count=stat.correction_count,
    )


def to_part_drawing_response(item: PartDrawing) -> PartDrawingResponse:
    advise = (
        POOR_GRADE_ADVISE_TEXT
        if item.status is PartDrawingStatus.ADVISE_MANUAL
        else None
    )
    out_of_scope = ASSEMBLY_OUT_OF_SCOPE_TEXT if item.is_assembly_or_exploded else None
    mark = LOW_QUALITY_MARK_TEXT if item.low_quality_unreliable else None
    review_fields = review_fields_for(item)
    unfinished = unfinished_confirmation_items(item)
    risk_fields = fields_for_risk_labels(item)
    return PartDrawingResponse(
        id=item.id,
        original_filename=item.original_filename,
        uploaded_at=item.uploaded_at,
        content_type=item.content_type,
        byte_size=item.byte_size,
        page_count=item.page_count,
        selected_page=item.selected_page,
        status=item.status,
        quality_grade=item.quality_grade,
        is_assembly_or_exploded=item.is_assembly_or_exploded,
        low_quality_unreliable=item.low_quality_unreliable,
        auto_prefill_allowed=auto_prefill_allowed(item),
        quality_grade_disclaimer=QUALITY_GRADE_DISCLAIMER,
        advise_manual_message=advise,
        out_of_scope_message=out_of_scope,
        low_quality_mark=mark,
        extracted_fields=[
            ExtractedFieldResponse(
                key=field.key,
                label=field.label,
                value=field.value,
                category=field.category,
                requires_confirmation=field.requires_confirmation,
                confirmed=field.confirmed,
                ignored=field.ignored,
                source=field.source,
            )
            for field in review_fields
        ],
        extraction_failure_reason=item.extraction_failure_reason,
        look_at_drawing_disclaimer=LOOK_AT_DRAWING_DISCLAIMER,
        risk_labels=[
            RiskLabelResponse(
                name=label.name,
                rule_id=label.rule_id,
                triggering_value=label.triggering_value,
                reason=label.reason,
            )
            for label in evaluate_risk_labels(risk_fields)
        ],
        no_judgable_risk_message=NO_JUDGABLE_RISK_ITEMS_MESSAGE,
        pending_confirmation_count=len(unfinished),
        pending_confirmation_labels=[field.label for field in unfinished],
    )
