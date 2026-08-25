from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from quote_assistant.domain.entities import Actor, PartDrawing
from quote_assistant.domain.errors import PartDrawingNotFound
from quote_assistant.usecase.ports import PartDrawingRepository, QuoteTaskRepository, UnitOfWork
from quote_assistant.usecase.tenant import (
    TenantBoundUseCase,
    require_visible_drawing,
    require_visible_quote_task,
)


class AssignPartDrawingToQuoteTask(TenantBoundUseCase):
    """Assign, move, or unassign a 零件图. quote_task_id=None means 移出."""

    def __init__(
        self,
        actor: Actor,
        quote_tasks: QuoteTaskRepository,
        drawings: PartDrawingRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._quote_tasks = quote_tasks
        self._drawings = drawings
        self._uow = uow

    def execute(self, drawing_id: UUID, quote_task_id: UUID | None) -> PartDrawing:
        drawing = require_visible_drawing(
            self.actor, self._drawings.get_for_tenant(self.tenant, drawing_id)
        )
        if quote_task_id is not None:
            require_visible_quote_task(
                self.actor, self._quote_tasks.get_for_tenant(self.tenant, quote_task_id)
            )
        updated = replace(drawing, quote_task_id=quote_task_id)
        self._drawings.save(updated)
        self._uow.commit()
        return updated


class RemovePartDrawingFromQuoteTask(TenantBoundUseCase):
    """Remove a 零件图 from a 报价任务. The drawing then belongs to none."""

    def __init__(
        self,
        actor: Actor,
        quote_tasks: QuoteTaskRepository,
        drawings: PartDrawingRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._assign = AssignPartDrawingToQuoteTask(
            actor=actor,
            quote_tasks=quote_tasks,
            drawings=drawings,
            uow=uow,
        )
        self._drawings = drawings
        self._quote_tasks = quote_tasks

    def execute(self, quote_task_id: UUID, drawing_id: UUID) -> PartDrawing:
        require_visible_quote_task(
            self.actor, self._quote_tasks.get_for_tenant(self.tenant, quote_task_id)
        )
        drawing = require_visible_drawing(
            self.actor, self._drawings.get_for_tenant(self.tenant, drawing_id)
        )
        if drawing.quote_task_id != quote_task_id:
            raise PartDrawingNotFound()
        return self._assign.execute(drawing_id, None)
