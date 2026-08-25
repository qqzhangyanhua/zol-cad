from __future__ import annotations

from quote_assistant.domain.entities import Actor, PartDrawing
from quote_assistant.usecase.ports import PartDrawingRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase, filter_owned_by_actor


class ListPartDrawings(TenantBoundUseCase):
    """List 零件图 for the authenticated Actor.

    Tenant comes from Actor. 报价员 only see drawings they themselves handled;
    管理员 see the whole factory. execute() takes no factory id.
    """

    def __init__(self, actor: Actor, drawings: PartDrawingRepository) -> None:
        super().__init__(actor)
        self._drawings = drawings

    def execute(self) -> list[PartDrawing]:
        return filter_owned_by_actor(
            self.actor,
            self._drawings.list_for_tenant(self.tenant),
            lambda drawing: drawing.uploaded_by_user_id,
        )
