from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar
from uuid import UUID

from quote_assistant.domain.entities import Actor, PartDrawing, Role
from quote_assistant.domain.errors import AdminRequired, PartDrawingNotFound, QuoteTaskNotFound
from quote_assistant.domain.quote_task import QuoteTask

T = TypeVar("T")


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


def require_admin(actor: Actor, message: str | None = None) -> None:
    """管理员专属能力；租户边界仍由 TenantScope 保证。"""
    if actor.role is not Role.ADMIN:
        raise AdminRequired(message or "只有管理员可以查看或录入本厂处理耗时与人工基线")


def actor_can_see_owned(actor: Actor, owner_user_id: UUID | None) -> bool:
    """管理员看全厂；报价员只看自己处理过的记录。"""
    if actor.role is Role.ADMIN:
        return True
    return owner_user_id == actor.user_id


def filter_owned_by_actor(
    actor: Actor,
    items: Sequence[T],
    owner_of: Callable[[T], UUID | None],
) -> list[T]:
    if actor.role is Role.ADMIN:
        return list(items)
    return [item for item in items if owner_of(item) == actor.user_id]


def require_visible_drawing(actor: Actor, drawing: PartDrawing | None) -> PartDrawing:
    if drawing is None or not actor_can_see_owned(actor, drawing.uploaded_by_user_id):
        raise PartDrawingNotFound()
    return drawing


def require_visible_quote_task(actor: Actor, task: QuoteTask | None) -> QuoteTask:
    if task is None or not actor_can_see_owned(actor, task.created_by_user_id):
        raise QuoteTaskNotFound()
    return task
