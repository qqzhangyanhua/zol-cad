from __future__ import annotations

from quote_assistant.domain.entities import Actor, PartDrawing
from quote_assistant.usecase.ports import PartDrawingRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase


class ListPartDrawings(TenantBoundUseCase):
    """List 零件图 for the authenticated 报价员's factory.

    execute() takes no factory id. The tenant scope is taken from the Actor.
    """

    def __init__(self, actor: Actor, drawings: PartDrawingRepository) -> None:
        super().__init__(actor)
        self._drawings = drawings

    def execute(self) -> list[PartDrawing]:
        return self._drawings.list_for_tenant(self.tenant)
