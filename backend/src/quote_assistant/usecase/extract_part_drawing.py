from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from quote_assistant.domain.entities import Actor, PartDrawing, PartDrawingStatus
from quote_assistant.domain.errors import (
    ExtractionValidationFailed,
    IllegalPartDrawingTransition,
)
from quote_assistant.domain.extraction import ExtractionRequest, merge_extraction_preserving_review
from quote_assistant.domain.part_drawing_state import record_transition
from quote_assistant.usecase.ports import (
    ExtractionEngine,
    ObjectStorage,
    PartDrawingEventRepository,
    PartDrawingRepository,
    UnitOfWork,
)
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_visible_drawing

_RETRYABLE = frozenset(
    {
        PartDrawingStatus.GRADED,
        PartDrawingStatus.EXTRACT_FAILED,
        PartDrawingStatus.EXTRACTED,
        PartDrawingStatus.REVIEWING,
    }
)
_ENGINE_FAILURE_REASON = "读图取数失败，请重试"


def apply_extraction(
    drawing: PartDrawing,
    *,
    actor_user_id: UUID | None,
    drawings: PartDrawingRepository,
    events: PartDrawingEventRepository,
    storage: ObjectStorage,
    engine: ExtractionEngine,
) -> PartDrawing:
    """提取中 → 已提取 / 提取失败. Caller owns the transaction."""
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

    try:
        page_content = storage.fetch(drawing.storage_key)
        result = engine.extract(
            ExtractionRequest(
                page_content=page_content,
                media_type=drawing.content_type,
                part_family_id=drawing.part_family_id,
                input_drawing_id=drawing.original_filename,
            )
        )
        drawing, finished = record_transition(
            drawing,
            PartDrawingStatus.EXTRACTED,
            occurred_at=datetime.now(UTC),
            sequence_no=events.next_sequence(drawing.id),
            actor_user_id=actor_user_id,
            extracted_fields=merge_extraction_preserving_review(
                drawing.extracted_fields,
                result.fields,
            ),
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


class ExtractPartDrawing(TenantBoundUseCase):
    """Start or retry 读图取数 using the already-stored 零件图. No re-upload."""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
        storage: ObjectStorage,
        engine: ExtractionEngine,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events
        self._storage = storage
        self._engine = engine
        self._uow = uow

    def execute(self, drawing_id: UUID) -> PartDrawing:
        drawing = require_visible_drawing(
            self.actor, self._drawings.get_for_tenant(self.tenant, drawing_id)
        )
        updated = apply_extraction(
            drawing,
            actor_user_id=self.actor.user_id,
            drawings=self._drawings,
            events=self._events,
            storage=self._storage,
            engine=self._engine,
        )
        self._uow.commit()
        return updated
