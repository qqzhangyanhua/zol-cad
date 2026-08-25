from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from quote_assistant.domain.entities import Actor, PartDrawing, PartDrawingStatus
from quote_assistant.domain.errors import IllegalPartDrawingTransition, PartDrawingNotFound
from quote_assistant.domain.part_drawing_state import record_transition
from quote_assistant.domain.quality import QualityGrade
from quote_assistant.usecase.extract_part_drawing import apply_extraction
from quote_assistant.usecase.ports import (
    ExtractionEngine,
    ObjectStorage,
    PartDrawingEventRepository,
    PartDrawingRepository,
    UnitOfWork,
)
from quote_assistant.usecase.tenant import TenantBoundUseCase


class ContinueDespitePoorQuality(TenantBoundUseCase):
    """Explicit 仍然继续: leave 建议人工 and re-enter the main path with a permanent mark."""

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
        drawing = self._drawings.get_for_tenant(self.tenant, drawing_id)
        if drawing is None:
            raise PartDrawingNotFound()
        if (
            drawing.status is not PartDrawingStatus.ADVISE_MANUAL
            or drawing.quality_grade is not QualityGrade.POOR
        ):
            raise IllegalPartDrawingTransition(
                "只有图纸质量分级为「差」且处于建议人工的零件图才能仍然继续"
            )
        sequence_no = self._events.next_sequence(drawing.id)
        updated, event = record_transition(
            drawing,
            PartDrawingStatus.GRADED,
            occurred_at=datetime.now(UTC),
            sequence_no=sequence_no,
            actor_user_id=self.actor.user_id,
            low_quality_unreliable=True,
        )
        self._drawings.save(updated)
        self._events.add(event)
        updated = apply_extraction(
            updated,
            actor_user_id=self.actor.user_id,
            drawings=self._drawings,
            events=self._events,
            storage=self._storage,
            engine=self._engine,
        )
        self._uow.commit()
        return updated
