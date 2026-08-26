from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from quote_assistant.domain.entities import PartDrawing, PartDrawingStatus
from quote_assistant.domain.errors import (
    ExtractionEngineFailed,
    ExtractionValidationFailed,
    IllegalPartDrawingTransition,
)
from quote_assistant.domain.extraction import (
    ExtractedField,
    ExtractionRequest,
    merge_extraction_preserving_review,
)
from quote_assistant.domain.part_drawing_state import record_transition
from quote_assistant.domain.part_family import adopt_content_classified_family
from quote_assistant.usecase.ports import (
    DrawingPageRenderer,
    ExtractionEngine,
    ObjectStorage,
    PartDrawingEventRepository,
    PartDrawingRepository,
    UnitOfWork,
)

_RETRYABLE = frozenset(
    {
        PartDrawingStatus.GRADED,
        PartDrawingStatus.EXTRACT_FAILED,
        PartDrawingStatus.EXTRACTED,
        PartDrawingStatus.REVIEWING,
    }
)
_ENGINE_FAILURE_REASON = "读图取数失败，请重试"


def build_extraction_request(
    drawing: PartDrawing,
    *,
    storage: ObjectStorage,
    renderer: DrawingPageRenderer,
) -> ExtractionRequest:
    """Fetch the stored 零件图 and hand the engine only 报价员指定的那一页."""
    page = renderer.render(
        storage.fetch(drawing.storage_key),
        drawing.content_type,
        drawing.selected_page,
    )
    return ExtractionRequest(
        page_content=page.content,
        media_type=page.media_type,
        part_family_id=drawing.part_family_id,
        input_drawing_id=drawing.original_filename,
    )


def apply_extraction(
    drawing: PartDrawing,
    *,
    actor_user_id: UUID | None,
    drawings: PartDrawingRepository,
    events: PartDrawingEventRepository,
    storage: ObjectStorage,
    renderer: DrawingPageRenderer,
    engine: ExtractionEngine,
    uow: UnitOfWork | None = None,
) -> PartDrawing:
    """提取中 → 已提取 / 提取失败.

    When *uow* is provided the 提取中 transition is committed before the engine
    call so a concurrent 重试 sees the in-progress status instead of starting a
    second paid run.
    """
    if drawing.status not in _RETRYABLE:
        raise IllegalPartDrawingTransition(
            f"零件图处于「{drawing.status.value}」，不能开始读图取数"
        )

    drawing, started = record_transition(
        drawing,
        PartDrawingStatus.EXTRACTING,
        occurred_at=datetime.now(UTC),
        sequence_no=events.next_sequence(drawing.id),
        actor_user_id=actor_user_id,
        extraction_failure_reason=None,
    )
    drawings.save(drawing)
    events.add(started)
    if uow is not None:
        uow.commit()

    try:
        fields = _fields_for_extraction(drawing, storage=storage, renderer=renderer, engine=engine)
        merged = merge_extraction_preserving_review(drawing.extracted_fields, fields)
        drawing = replace(
            drawing,
            part_family_id=adopt_content_classified_family(
                drawing.part_family_id,
                extracted_fields=merged,
            ),
        )
        drawing, finished = record_transition(
            drawing,
            PartDrawingStatus.EXTRACTED,
            occurred_at=datetime.now(UTC),
            sequence_no=events.next_sequence(drawing.id),
            actor_user_id=actor_user_id,
            extracted_fields=merged,
            stashed_extracted_fields=None,
            extraction_failure_reason=None,
        )
    except ExtractionValidationFailed as exc:
        drawing, finished = record_transition(
            drawing,
            PartDrawingStatus.EXTRACT_FAILED,
            occurred_at=datetime.now(UTC),
            sequence_no=events.next_sequence(drawing.id),
            actor_user_id=actor_user_id,
            extraction_failure_reason=str(exc),
        )
    except ExtractionEngineFailed as exc:
        drawing, finished = record_transition(
            drawing,
            PartDrawingStatus.EXTRACT_FAILED,
            occurred_at=datetime.now(UTC),
            sequence_no=events.next_sequence(drawing.id),
            actor_user_id=actor_user_id,
            extraction_failure_reason=str(exc),
        )
    except Exception:
        drawing, finished = record_transition(
            drawing,
            PartDrawingStatus.EXTRACT_FAILED,
            occurred_at=datetime.now(UTC),
            sequence_no=events.next_sequence(drawing.id),
            actor_user_id=actor_user_id,
            extraction_failure_reason=_ENGINE_FAILURE_REASON,
        )
    drawings.save(drawing)
    events.add(finished)
    return drawing


def _fields_for_extraction(
    drawing: PartDrawing,
    *,
    storage: ObjectStorage,
    renderer: DrawingPageRenderer,
    engine: ExtractionEngine,
) -> tuple[ExtractedField, ...]:
    """Reuse the first extract when 分级 already stashed it. Otherwise call the engine."""
    if drawing.stashed_extracted_fields is not None:
        return drawing.stashed_extracted_fields
    return engine.extract(
        build_extraction_request(drawing, storage=storage, renderer=renderer)
    ).fields
