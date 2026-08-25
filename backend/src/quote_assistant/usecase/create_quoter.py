from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from quote_assistant.domain.accounts import normalize_quoter_username, validate_quoter_password
from quote_assistant.domain.entities import Actor, Role, User
from quote_assistant.domain.errors import DuplicateUsername
from quote_assistant.usecase.ports import PasswordHasher, UnitOfWork, UserRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_admin


class CreateQuoter(TenantBoundUseCase):
    """管理员为本厂创建报价员账号。角色固定为报价员，不能在这里创建管理员。"""

    def __init__(
        self,
        actor: Actor,
        users: UserRepository,
        hasher: PasswordHasher,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._users = users
        self._hasher = hasher
        self._uow = uow

    def execute(self, username: str, password: str) -> User:
        require_admin(self.actor, "只有管理员可以创建本厂报价员账号")
        normalized = normalize_quoter_username(username)
        validate_quoter_password(password)
        if self._users.get_by_username(normalized) is not None:
            raise DuplicateUsername("账号已被占用")
        user = User(
            id=uuid4(),
            factory_id=self.tenant.factory_id,
            factory_name=self.actor.factory_name,
            username=normalized,
            role=Role.QUOTER,
            created_at=datetime.now(UTC),
            disabled_at=None,
        )
        self._users.add(user, self._hasher.hash_password(password))
        self._uow.commit()
        return user
