from __future__ import annotations

from uuid import UUID

from quote_assistant.domain.entities import Actor


class TenantScope:
    """Factory-bounded query scope.

    The only constructor argument is an authenticated Actor. Callers cannot
    supply a raw factory id, so a use case cannot accidentally (or maliciously)
    query another factory.
    """

    __slots__ = ("_factory_id",)

    def __init__(self, actor: Actor) -> None:
        if type(actor) is not Actor:
            raise TypeError("TenantScope 只能由已认证的 Actor 构造")
        self._factory_id = actor.factory_id

    @property
    def factory_id(self) -> UUID:
        return self._factory_id


class TenantBoundUseCase:
    """Every tenant-owned use case inherits this so the scope is always applied."""

    def __init__(self, actor: Actor) -> None:
        self.actor = actor
        self.tenant = TenantScope(actor)
