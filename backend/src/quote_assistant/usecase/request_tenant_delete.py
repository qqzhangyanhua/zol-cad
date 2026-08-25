from __future__ import annotations

from datetime import UTC, datetime
from secrets import token_urlsafe

from quote_assistant.domain.entities import Actor
from quote_assistant.domain.tenant_data import TenantDeleteChallenge, new_tenant_delete_challenge
from quote_assistant.usecase.ports import TenantDeleteChallengeRepository, UnitOfWork
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_admin


class RequestTenantDelete(TenantBoundUseCase):
    """Issue a one-time delete confirmation for this factory. Tenant comes from Actor."""

    def __init__(
        self,
        actor: Actor,
        challenges: TenantDeleteChallengeRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._challenges = challenges
        self._uow = uow

    def execute(self) -> TenantDeleteChallenge:
        require_admin(self.actor, "只有管理员可以删除本厂数据")
        challenge = new_tenant_delete_challenge(
            factory_id=self.tenant.factory_id,
            factory_name=self.actor.factory_name,
            actor_user_id=self.actor.user_id,
            token=token_urlsafe(32),
            now=datetime.now(UTC),
        )
        self._challenges.add(challenge)
        self._uow.commit()
        return challenge
