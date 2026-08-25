from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from quote_assistant.domain.entities import Actor, PartDrawing
from quote_assistant.domain.errors import PartDrawingNotFound
from quote_assistant.domain.review import (
    begin_reviewing,
    complete_review,
    confirm_extracted_field,
    edit_extracted_field,
)
from quote_assistant.usecase.ports import PartDrawingEventRepository, PartDrawingRepository, UnitOfWork
from quote_assistant.usecase.tenant import TenantBoundUseCase, TenantScope


def _load_for_tenant(
    drawings: PartDrawingRepository,
    tenant: TenantScope,
    drawing_id: UUID,
) -> PartDrawing:
    drawing = drawings.get_for_tenant(tenant, drawing_id)
    if drawing is None:
        raise PartDrawingNotFound()
    return drawing


def _save_review_action(
    mutated: PartDrawing,
    *,
    actor_user_id: UUID,
    drawings: PartDrawingRepository,
    events: PartDrawingEventRepository,
) -> PartDrawing:
    drawing, started = begin_reviewing(
        mutated,
        occurred_at=datetime.now(UTC),
        sequence_no=events.next_sequence(mutated.id),
        actor_user_id=actor_user_id,
    )
    drawings.save(drawing)
    if started is not None:
        events.add(started)
    return drawing


class ConfirmExtractedField(TenantBoundUseCase):
    """报价员逐项点击确认。"""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events
        self._uow = uow

    def execute(self, drawing_id: UUID, field_key: str) -> PartDrawing:
        drawing = _load_for_tenant(self._drawings, self.tenant, drawing_id)
        drawing = _save_review_action(
            confirm_extracted_field(drawing, field_key),
            actor_user_id=self.actor.user_id,
            drawings=self._drawings,
            events=self._events,
        )
        self._uow.commit()
        return drawing


class UpdateExtractedField(TenantBoundUseCase):
    """报价员就地修改提取值；修改立即落库。"""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events
        self._uow = uow

    def execute(self, drawing_id: UUID, field_key: str, value: str | None) -> PartDrawing:
        drawing = _load_for_tenant(self._drawings, self.tenant, drawing_id)
        drawing = _save_review_action(
            edit_extracted_field(drawing, field_key, value),
            actor_user_id=self.actor.user_id,
            drawings=self._drawings,
            events=self._events,
        )
        self._uow.commit()
        return drawing


class CompleteReview(TenantBoundUseCase):
    """全部需确认项处理完后，把零件图标记为已复核。"""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events
        self._uow = uow

    def execute(self, drawing_id: UUID) -> PartDrawing:
        drawing = _load_for_tenant(self._drawings, self.tenant, drawing_id)
        drawing, event = complete_review(
            drawing,
            occurred_at=datetime.now(UTC),
            sequence_no=self._events.next_sequence(drawing.id),
            actor_user_id=self.actor.user_id,
        )
        self._drawings.save(drawing)
        self._events.add(event)
        self._uow.commit()
        return drawing
