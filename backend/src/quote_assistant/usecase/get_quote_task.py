from __future__ import annotations

from uuid import UUID

from quote_assistant.domain.entities import Actor
from quote_assistant.domain.errors import QuoteTaskNotFound
from quote_assistant.domain.quote_task import QuoteTaskView, assemble_quote_task_view
from quote_assistant.usecase.ports import PartDrawingRepository, QuoteTaskRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase


class GetQuoteTask(TenantBoundUseCase):
    """Load one 报价任务 and its 零件图 for the authenticated 报价员's factory."""

    def __init__(
        self,
        actor: Actor,
        quote_tasks: QuoteTaskRepository,
        drawings: PartDrawingRepository,
    ) -> None:
        super().__init__(actor)
        self._quote_tasks = quote_tasks
        self._drawings = drawings

    def execute(self, quote_task_id: UUID) -> QuoteTaskView:
        task = self._quote_tasks.get_for_tenant(self.tenant, quote_task_id)
        if task is None:
            raise QuoteTaskNotFound()
        drawings = self._drawings.list_for_quote_task(self.tenant, quote_task_id)
        return assemble_quote_task_view(task, drawings)
