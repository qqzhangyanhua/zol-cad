from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from quote_assistant.domain.entities import Actor, OriginalAccess
from quote_assistant.domain.errors import PartDrawingNotFound
from quote_assistant.usecase.ports import ObjectStorage, PartDrawingRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase


class IssueOriginalAccessUrl(TenantBoundUseCase):
    """Issue a short-lived URL for the original 零件图. Tenant comes from Actor."""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        storage: ObjectStorage,
        ttl: timedelta,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._storage = storage
        self._ttl = ttl

    def execute(self, drawing_id: UUID) -> OriginalAccess:
        drawing = self._drawings.get_for_tenant(self.tenant, drawing_id)
        if drawing is None:
            raise PartDrawingNotFound()
        url = self._storage.sign_access_url(drawing.storage_key, self._ttl)
        return OriginalAccess(
            drawing=drawing,
            url=url,
            expires_at=datetime.now(UTC) + self._ttl,
        )
