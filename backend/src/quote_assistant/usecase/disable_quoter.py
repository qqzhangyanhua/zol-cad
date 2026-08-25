from __future__ import annotations

from uuid import UUID

from quote_assistant.domain.entities import Actor, Role, User
from quote_assistant.domain.errors import InvalidAccount, UserNotFound
from quote_assistant.usecase.ports import SessionRepository, UnitOfWork, UserRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_admin


class DisableQuoter(TenantBoundUseCase):
    """管理员停用本厂报价员。不能停用管理员，也不能跨厂。"""

    def __init__(
        self,
        actor: Actor,
        users: UserRepository,
        sessions: SessionRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._users = users
        self._sessions = sessions
        self._uow = uow

    def execute(self, user_id: UUID) -> User:
        require_admin(self.actor, "只有管理员可以停用本厂报价员账号")
        user = self._users.get_by_id(user_id)
        if user is None or user.factory_id != self.tenant.factory_id:
            raise UserNotFound()
        if user.role is not Role.QUOTER:
            raise InvalidAccount("只能停用报价员账号")
        disabled = self._users.disable(self.tenant, user.id)
        if disabled is None:
            raise UserNotFound()
        self._sessions.revoke_for_user(user.id)
        self._uow.commit()
        return disabled
