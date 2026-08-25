from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID, uuid4

from quote_assistant.domain.entities import PartDrawing, PartDrawingStatus
from quote_assistant.domain.errors import IllegalPartDrawingTransition
from quote_assistant.domain.extraction import ExtractedField, ExtractionResult
from quote_assistant.domain.quality import QualityGrade

_UNSET = object()


LEGAL_TRANSITIONS: frozenset[tuple[PartDrawingStatus | None, PartDrawingStatus]] = frozenset(
    {
        (None, PartDrawingStatus.UPLOADED),
        (PartDrawingStatus.UPLOADED, PartDrawingStatus.GRADING),
        (PartDrawingStatus.GRADING, PartDrawingStatus.GRADED),
        (PartDrawingStatus.GRADING, PartDrawingStatus.ADVISE_MANUAL),
        (PartDrawingStatus.GRADING, PartDrawingStatus.OUT_OF_SCOPE),
        (PartDrawingStatus.ADVISE_MANUAL, PartDrawingStatus.GRADED),
        (PartDrawingStatus.GRADED, PartDrawingStatus.EXTRACTING),
        (PartDrawingStatus.EXTRACTING, PartDrawingStatus.EXTRACTED),
        (PartDrawingStatus.EXTRACTING, PartDrawingStatus.EXTRACT_FAILED),
        (PartDrawingStatus.EXTRACT_FAILED, PartDrawingStatus.EXTRACTING),
    }
)


@dataclass(frozen=True)
class PartDrawingEvent:
    id: UUID
    part_drawing_id: UUID
    factory_id: UUID
    from_status: PartDrawingStatus | None
    to_status: PartDrawingStatus
    occurred_at: datetime
    sequence_no: int
    actor_user_id: UUID | None


def status_after_grade(result: ExtractionResult) -> PartDrawingStatus:
    if result.is_assembly_or_exploded:
        return PartDrawingStatus.OUT_OF_SCOPE
    if result.quality_grade is QualityGrade.POOR:
        return PartDrawingStatus.ADVISE_MANUAL
    return PartDrawingStatus.GRADED


_PREFILL_PATH = frozenset(
    {
        PartDrawingStatus.GRADED,
        PartDrawingStatus.EXTRACTING,
        PartDrawingStatus.EXTRACTED,
        PartDrawingStatus.EXTRACT_FAILED,
    }
)


def auto_prefill_allowed(drawing: PartDrawing) -> bool:
    """差图与装配/爆炸图不自动预填；显式覆盖回到主干后才允许继续处理。"""
    return drawing.status in _PREFILL_PATH and not drawing.is_assembly_or_exploded


def _require_legal(from_status: PartDrawingStatus | None, to_status: PartDrawingStatus) -> None:
    if (from_status, to_status) not in LEGAL_TRANSITIONS:
        current = from_status.value if from_status is not None else "（无）"
        raise IllegalPartDrawingTransition(f"零件图不能从「{current}」迁移到「{to_status.value}」")


def _event(
    *,
    drawing: PartDrawing,
    from_status: PartDrawingStatus | None,
    to_status: PartDrawingStatus,
    occurred_at: datetime,
    sequence_no: int,
    actor_user_id: UUID | None,
) -> PartDrawingEvent:
    return PartDrawingEvent(
        id=uuid4(),
        part_drawing_id=drawing.id,
        factory_id=drawing.factory_id,
        from_status=from_status,
        to_status=to_status,
        occurred_at=occurred_at,
        sequence_no=sequence_no,
        actor_user_id=actor_user_id,
    )


def record_transition(
    drawing: PartDrawing,
    to_status: PartDrawingStatus,
    *,
    occurred_at: datetime,
    sequence_no: int,
    actor_user_id: UUID | None,
    quality_grade: QualityGrade | None = None,
    is_assembly_or_exploded: bool | None = None,
    low_quality_unreliable: bool | None = None,
    extracted_fields: tuple[ExtractedField, ...] | None = None,
    extraction_failure_reason: str | None | object = _UNSET,
) -> tuple[PartDrawing, PartDrawingEvent]:
    _require_legal(drawing.status, to_status)
    updates: dict[str, object] = {"status": to_status}
    if quality_grade is not None:
        updates["quality_grade"] = quality_grade
    if is_assembly_or_exploded is not None:
        updates["is_assembly_or_exploded"] = is_assembly_or_exploded
    if low_quality_unreliable is not None:
        updates["low_quality_unreliable"] = low_quality_unreliable
    if extracted_fields is not None:
        updates["extracted_fields"] = extracted_fields
    if extraction_failure_reason is not _UNSET:
        updates["extraction_failure_reason"] = extraction_failure_reason
    updated = replace(drawing, **updates)
    return updated, _event(
        drawing=updated,
        from_status=drawing.status,
        to_status=to_status,
        occurred_at=occurred_at,
        sequence_no=sequence_no,
        actor_user_id=actor_user_id,
    )


def birth_uploaded(
    drawing: PartDrawing,
    *,
    occurred_at: datetime,
    actor_user_id: UUID | None,
) -> tuple[PartDrawing, PartDrawingEvent]:
    """First event: the 零件图 is born already in 已上传. Status must be 已上传."""
    if drawing.status is not PartDrawingStatus.UPLOADED:
        raise IllegalPartDrawingTransition("新建零件图的起始状态必须是「已上传」")
    _require_legal(None, PartDrawingStatus.UPLOADED)
    return drawing, _event(
        drawing=drawing,
        from_status=None,
        to_status=PartDrawingStatus.UPLOADED,
        occurred_at=occurred_at,
        sequence_no=1,
        actor_user_id=actor_user_id,
    )
