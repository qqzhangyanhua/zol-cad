from __future__ import annotations

from collections.abc import Sequence

from quote_assistant.domain.entities import Actor
from quote_assistant.domain.factory_preferences import (
    FactoryPreferences,
    default_factory_preferences,
    normalize_risk_label_priority,
)
from quote_assistant.usecase.ports import FactoryPreferenceRepository, UnitOfWork
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_admin


class ReplaceRiskLabelPriority(TenantBoundUseCase):
    """管理员设置本厂风险标签展示顺序。只影响展示，不影响规则是否触发。"""

    def __init__(
        self,
        actor: Actor,
        preferences: FactoryPreferenceRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._preferences = preferences
        self._uow = uow

    def execute(self, names: Sequence[str]) -> FactoryPreferences:
        require_admin(self.actor, "只有管理员可以调整风险标签展示优先级")
        current = self._preferences.get_for_tenant(self.tenant) or default_factory_preferences(
            self.tenant.factory_id
        )
        updated = FactoryPreferences(
            factory_id=self.tenant.factory_id,
            common_materials=current.common_materials,
            risk_label_priority=normalize_risk_label_priority(names),
        )
        self._preferences.save_for_tenant(self.tenant, updated)
        self._uow.commit()
        return updated
