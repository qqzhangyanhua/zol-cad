from __future__ import annotations

from uuid import UUID

from quote_assistant.domain.entities import Actor, PartDrawing
from quote_assistant.domain.errors import PartDrawingNotFound
from quote_assistant.usecase.ports import PartDrawingRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase


class GetPartDrawing(TenantBoundUseCase):
    """Load one 零件图 for the authenticated 报价员's factory."""

    def __init__(self, actor: Actor, drawings: PartDrawingRepository) -> None:
        super().__init__(actor)
        self._drawings = drawings

    def execute(self, drawing_id: UUID) -> PartDrawing:
        drawing = self._drawings.get_for_tenant(self.tenant, drawing_id)
        if drawing is None:
            raise PartDrawingNotFound()
        return drawing
