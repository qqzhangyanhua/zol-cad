from __future__ import annotations

from collections.abc import Sequence

from quote_assistant.domain.entities import Actor
from quote_assistant.domain.factory_preferences import (
    FactoryPreferences,
    default_factory_preferences,
    normalize_common_materials,
)
from quote_assistant.usecase.ports import FactoryPreferenceRepository, UnitOfWork
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_admin


class ReplaceCommonMaterials(TenantBoundUseCase):
    """管理员整表替换本厂常用材料。复核时作为材料字段候选。"""

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
        require_admin(self.actor, "只有管理员可以配置本厂常用材料")
        current = self._preferences.get_for_tenant(self.tenant) or default_factory_preferences(
            self.tenant.factory_id
        )
        updated = FactoryPreferences(
            factory_id=self.tenant.factory_id,
            common_materials=normalize_common_materials(names),
            risk_label_priority=current.risk_label_priority,
        )
        self._preferences.save_for_tenant(self.tenant, updated)
        self._uow.commit()
        return updated
