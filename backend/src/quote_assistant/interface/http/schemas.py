from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from quote_assistant.domain.correction import CorrectionFieldTypeStat, CorrectionRecord
from quote_assistant.domain.entities import (
    DrawingProcessingTime,
    ManualBaseline,
    PartDrawing,
    PartDrawingStatus,
    ProcessingTimeComparison,
    Role,
)
from quote_assistant.domain.extraction import (
    LOOK_AT_DRAWING_DISCLAIMER,
    FieldCategory,
    FieldSource,
)
from quote_assistant.domain.part_family import experimental_mark_for, is_target_part_family
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
from quote_assistant.domain.quote_task import QuoteTaskReviewStatus, QuoteTaskView
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
    part_family_id: str
    is_target_part_family: bool
    experimental_mark: str | None
    risk_labels: list[RiskLabelResponse]
    no_judgable_risk_message: str
    pending_confirmation_count: int
    pending_confirmation_labels: list[str]
    quote_task_id: UUID | None


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


class RecordManualBaselineRequest(BaseModel):
    part_description: str = Field(min_length=1, max_length=200)
    manual_duration_seconds: int = Field(gt=0, le=24 * 60 * 60)


class ManualBaselineResponse(BaseModel):
    id: UUID
    part_description: str
    manual_duration_seconds: int
    recorded_at: datetime


class DrawingProcessingTimeResponse(BaseModel):
    part_drawing_id: UUID
    original_filename: str
    uploaded_at: datetime
    reviewed_at: datetime
    processing_seconds: float
    grading_seconds: float | None
    extraction_seconds: float | None
    review_seconds: float | None


class ProcessingTimeComparisonResponse(BaseModel):
    reviewed_count: int
    excluded_unreviewed_count: int
    average_processing_seconds: float | None
    average_grading_seconds: float | None
    average_extraction_seconds: float | None
    average_review_seconds: float | None
    baseline_count: int
    average_baseline_seconds: float | None
    saved_seconds: float | None
    items: list[DrawingProcessingTimeResponse]
    baselines: list[ManualBaselineResponse]


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
        part_family_id=item.part_family_id,
        is_target_part_family=is_target_part_family(item.part_family_id),
        experimental_mark=experimental_mark_for(item.part_family_id),
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
        quote_task_id=item.quote_task_id,
    )


class CreateQuoteTaskRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    customer_name: str = Field(min_length=1, max_length=200)


class AssignPartDrawingRequest(BaseModel):
    part_drawing_id: UUID


class QuoteTaskSummaryResponse(BaseModel):
    id: UUID
    name: str
    customer_name: str
    created_at: datetime
    review_status: QuoteTaskReviewStatus
    drawing_count: int


class QuoteTaskListResponse(BaseModel):
    items: list[QuoteTaskSummaryResponse]


class QuoteTaskDetailResponse(BaseModel):
    id: UUID
    name: str
    customer_name: str
    created_at: datetime
    review_status: QuoteTaskReviewStatus
    drawings: list[PartDrawingResponse]


def to_quote_task_summary_response(view: QuoteTaskView) -> QuoteTaskSummaryResponse:
    return QuoteTaskSummaryResponse(
        id=view.task.id,
        name=view.task.name,
        customer_name=view.task.customer_name,
        created_at=view.task.created_at,
        review_status=view.review_status,
        drawing_count=view.drawing_count,
    )


def to_quote_task_detail_response(view: QuoteTaskView) -> QuoteTaskDetailResponse:
    return QuoteTaskDetailResponse(
        id=view.task.id,
        name=view.task.name,
        customer_name=view.task.customer_name,
        created_at=view.task.created_at,
        review_status=view.review_status,
        drawings=[to_part_drawing_response(drawing) for drawing in view.drawings],
    )


def to_manual_baseline_response(item: ManualBaseline) -> ManualBaselineResponse:
    return ManualBaselineResponse(
        id=item.id,
        part_description=item.part_description,
        manual_duration_seconds=item.manual_duration_seconds,
        recorded_at=item.recorded_at,
    )


def to_drawing_processing_time_response(item: DrawingProcessingTime) -> DrawingProcessingTimeResponse:
    return DrawingProcessingTimeResponse(
        part_drawing_id=item.part_drawing_id,
        original_filename=item.original_filename,
        uploaded_at=item.uploaded_at,
        reviewed_at=item.reviewed_at,
        processing_seconds=item.processing_seconds,
        grading_seconds=item.grading_seconds,
        extraction_seconds=item.extraction_seconds,
        review_seconds=item.review_seconds,
    )


def to_processing_time_comparison_response(
    item: ProcessingTimeComparison,
) -> ProcessingTimeComparisonResponse:
    return ProcessingTimeComparisonResponse(
        reviewed_count=item.reviewed_count,
        excluded_unreviewed_count=item.excluded_unreviewed_count,
        average_processing_seconds=item.average_processing_seconds,
        average_grading_seconds=item.average_grading_seconds,
        average_extraction_seconds=item.average_extraction_seconds,
        average_review_seconds=item.average_review_seconds,
        baseline_count=item.baseline_count,
        average_baseline_seconds=item.average_baseline_seconds,
        saved_seconds=item.saved_seconds,
        items=[to_drawing_processing_time_response(row) for row in item.items],
        baselines=[to_manual_baseline_response(row) for row in item.baselines],
    )
