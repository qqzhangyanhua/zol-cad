from __future__ import annotations

from uuid import UUID

from quote_assistant.domain.entities import Actor, Role
from quote_assistant.domain.errors import AdminRequired


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


def require_admin(actor: Actor) -> None:
    """处理耗时与人工基线只对管理员开放；租户边界仍由 TenantScope 保证。"""
    if actor.role is not Role.ADMIN:
        raise AdminRequired("只有管理员可以查看或录入本厂处理耗时与人工基线")
