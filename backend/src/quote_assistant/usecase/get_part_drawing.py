from __future__ import annotations

from uuid import UUID

from quote_assistant.domain.entities import Actor, PartDrawing
from quote_assistant.usecase.ports import PartDrawingRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_visible_drawing


class GetPartDrawing(TenantBoundUseCase):
    """Load one 零件图 the Actor may see: own for 报价员, factory-wide for 管理员."""

    def __init__(self, actor: Actor, drawings: PartDrawingRepository) -> None:
        super().__init__(actor)
        self._drawings = drawings

    def execute(self, drawing_id: UUID) -> PartDrawing:
        return require_visible_drawing(
            self.actor, self._drawings.get_for_tenant(self.tenant, drawing_id)
        )
