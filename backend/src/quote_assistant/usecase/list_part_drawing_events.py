from __future__ import annotations

from uuid import UUID

from quote_assistant.domain.entities import Actor
from quote_assistant.domain.part_drawing_state import PartDrawingEvent
from quote_assistant.usecase.ports import PartDrawingEventRepository, PartDrawingRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_visible_drawing


class ListPartDrawingEvents(TenantBoundUseCase):
    """List timestamped state-machine events of one 零件图 in the Actor's factory."""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events

    def execute(self, drawing_id: UUID) -> list[PartDrawingEvent]:
        drawing = require_visible_drawing(
            self.actor, self._drawings.get_for_tenant(self.tenant, drawing_id)
        )
        return self._events.list_for_drawing(self.tenant, drawing.id)
