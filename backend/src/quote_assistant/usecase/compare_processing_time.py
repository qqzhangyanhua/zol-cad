from __future__ import annotations

from quote_assistant.domain.entities import Actor, ProcessingTimeComparison
from quote_assistant.domain.processing_time import compare_processing_time
from quote_assistant.usecase.ports import (
    ManualBaselineRepository,
    PartDrawingEventRepository,
    PartDrawingRepository,
)
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_admin


class CompareProcessingTime(TenantBoundUseCase):
    """本厂已复核零件图的处理耗时，对照管理员录入的人工基线。"""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
        baselines: ManualBaselineRepository,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events
        self._baselines = baselines

    def execute(self) -> ProcessingTimeComparison:
        require_admin(self.actor)
        return compare_processing_time(
            self._drawings.list_for_tenant(self.tenant),
            self._events.list_for_tenant(self.tenant),
            self._baselines.list_for_tenant(self.tenant),
        )
