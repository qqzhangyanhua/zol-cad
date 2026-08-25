from __future__ import annotations

from uuid import UUID

from quote_assistant.domain.correction import CorrectionRecord
from quote_assistant.domain.entities import Actor
from quote_assistant.usecase.ports import CorrectionRecordRepository, PartDrawingRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_visible_drawing


class ListCorrectionRecords(TenantBoundUseCase):
    """Read 修正记录 of one 零件图 in the Actor's factory. Tenant-filtered."""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        corrections: CorrectionRecordRepository,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._corrections = corrections

    def execute(self, drawing_id: UUID) -> list[CorrectionRecord]:
        drawing = require_visible_drawing(
            self.actor, self._drawings.get_for_tenant(self.tenant, drawing_id)
        )
        return self._corrections.list_for_drawing(self.tenant, drawing.id)
