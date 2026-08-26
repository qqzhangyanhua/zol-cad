from __future__ import annotations

from datetime import UTC, datetime

from quote_assistant.domain.entities import Actor
from quote_assistant.domain.errors import TenantDeleteConfirmationInvalid
from quote_assistant.domain.tenant_data import (
    TENANT_DELETE_CONFIRMATION_INVALID_MESSAGE,
    confirmation_accepted,
)
from quote_assistant.usecase.ports import (
    ObjectStorage,
    PartDrawingRepository,
    TenantDataPurge,
    TenantDeleteChallengeRepository,
    UnitOfWork,
)
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_admin


class DeleteTenantData(TenantBoundUseCase):
    """Delete this factory's operational data after a server-checked second confirmation."""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        challenges: TenantDeleteChallengeRepository,
        purge: TenantDataPurge,
        storage: ObjectStorage,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._challenges = challenges
        self._purge = purge
        self._storage = storage
        self._uow = uow

    def execute(self, confirm_token: str, confirm_phrase: str) -> None:
        require_admin(self.actor, "只有管理员可以删除本厂数据")
        now = datetime.now(UTC)
        challenge = self._challenges.get_open(self.tenant, confirm_token, now)
        if challenge is None or not confirmation_accepted(
            expected_token=challenge.token,
            submitted_token=confirm_token,
            expected_phrase=challenge.required_phrase,
            submitted_phrase=confirm_phrase,
        ):
            raise TenantDeleteConfirmationInvalid(TENANT_DELETE_CONFIRMATION_INVALID_MESSAGE)
        storage_keys = [
            drawing.storage_key for drawing in self._drawings.list_for_tenant(self.tenant)
        ]
        self._challenges.mark_consumed(self.tenant, challenge.token, now)
        self._purge.delete_operational_data(self.tenant)
        self._uow.commit()
        for key in storage_keys:
            self._storage.delete(key)
