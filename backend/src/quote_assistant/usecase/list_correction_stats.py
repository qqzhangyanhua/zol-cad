from __future__ import annotations

from dataclasses import dataclass

from quote_assistant.domain.correction import (
    CORRECTION_STATS_PURPOSE,
    CorrectionFieldTypeStat,
    aggregate_correction_stats,
)
from quote_assistant.domain.entities import Actor, Role
from quote_assistant.domain.errors import AdminRequired
from quote_assistant.usecase.ports import CorrectionRecordRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase


@dataclass(frozen=True)
class CorrectionStatsResult:
    items: tuple[CorrectionFieldTypeStat, ...]
    purpose: str


class ListCorrectionStats(TenantBoundUseCase):
    """管理员查看本厂修正记录按字段类型聚合的频次。"""

    def __init__(self, actor: Actor, corrections: CorrectionRecordRepository) -> None:
        super().__init__(actor)
        self._corrections = corrections

    def execute(self) -> CorrectionStatsResult:
        if self.actor.role is not Role.ADMIN:
            raise AdminRequired("只有管理员可以查看全厂修正记录统计")
        records = self._corrections.list_for_tenant(self.tenant)
        return CorrectionStatsResult(
            items=aggregate_correction_stats(records),
            purpose=CORRECTION_STATS_PURPOSE,
        )
