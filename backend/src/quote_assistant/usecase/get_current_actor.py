from __future__ import annotations

from quote_assistant.domain.entities import Actor
from quote_assistant.usecase.tenant import TenantBoundUseCase


class GetCurrentActor(TenantBoundUseCase):
    """Return the already-resolved Actor. No extra lookup, no caller-supplied tenant."""

    def execute(self) -> Actor:
        return self.actor
