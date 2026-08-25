from __future__ import annotations

from quote_assistant.domain.entities import Actor
from quote_assistant.domain.factory_preferences import (
    FactoryPreferences,
    default_factory_preferences,
)
from quote_assistant.usecase.ports import FactoryPreferenceRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase


class GetFactoryPreferences(TenantBoundUseCase):
    """本厂常用材料与风险标签展示优先级。任何本厂角色可读，供复核候选使用。"""

    def __init__(self, actor: Actor, preferences: FactoryPreferenceRepository) -> None:
        super().__init__(actor)
        self._preferences = preferences

    def execute(self) -> FactoryPreferences:
        stored = self._preferences.get_for_tenant(self.tenant)
        if stored is None:
            return default_factory_preferences(self.tenant.factory_id)
        return stored
