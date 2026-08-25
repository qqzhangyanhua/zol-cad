from __future__ import annotations

from quote_assistant.domain.entities import Actor, User
from quote_assistant.usecase.ports import UserRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_admin


class ListFactoryAccounts(TenantBoundUseCase):
    """管理员查看本厂账号。租户来自 Actor。"""

    def __init__(self, actor: Actor, users: UserRepository) -> None:
        super().__init__(actor)
        self._users = users

    def execute(self) -> list[User]:
        require_admin(self.actor, "只有管理员可以查看本厂账号")
        return self._users.list_for_tenant(self.tenant)
