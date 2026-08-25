from __future__ import annotations

from datetime import UTC, datetime

from quote_assistant.domain.entities import Actor, ManualBaseline
from quote_assistant.domain.processing_time import new_manual_baseline
from quote_assistant.usecase.ports import ManualBaselineRepository, UnitOfWork
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_admin


class RecordManualBaseline(TenantBoundUseCase):
    """管理员录入一条纯人工作业计时，作为处理耗时对照。"""

    def __init__(
        self,
        actor: Actor,
        baselines: ManualBaselineRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._baselines = baselines
        self._uow = uow

    def execute(self, part_description: str, manual_duration_seconds: int) -> ManualBaseline:
        require_admin(self.actor)
        baseline = new_manual_baseline(
            factory_id=self.tenant.factory_id,
            part_description=part_description,
            manual_duration_seconds=manual_duration_seconds,
            recorded_at=datetime.now(UTC),
            recorded_by_user_id=self.actor.user_id,
        )
        self._baselines.add(baseline)
        self._uow.commit()
        return baseline
