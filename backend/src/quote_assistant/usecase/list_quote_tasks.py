from __future__ import annotations

from datetime import datetime

from quote_assistant.domain.entities import Actor
from quote_assistant.domain.quote_task import (
    QuoteTaskReviewStatus,
    QuoteTaskView,
    assemble_quote_task_view,
)
from quote_assistant.usecase.ports import PartDrawingRepository, QuoteTaskRepository
from quote_assistant.usecase.tenant import TenantBoundUseCase, filter_owned_by_actor


class ListQuoteTasks(TenantBoundUseCase):
    """List 报价任务 of the Actor's factory. Filters never include a factory id."""

    def __init__(
        self,
        actor: Actor,
        quote_tasks: QuoteTaskRepository,
        drawings: PartDrawingRepository,
    ) -> None:
        super().__init__(actor)
        self._quote_tasks = quote_tasks
        self._drawings = drawings

    def execute(
        self,
        customer_name: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        review_status: QuoteTaskReviewStatus | None = None,
    ) -> list[QuoteTaskView]:
        tasks = filter_owned_by_actor(
            self.actor,
            self._quote_tasks.list_for_tenant(
                self.tenant,
                customer_name=customer_name.strip() if customer_name else None,
                created_from=created_from,
                created_to=created_to,
            ),
            lambda task: task.created_by_user_id,
        )
        drawings = filter_owned_by_actor(
            self.actor,
            self._drawings.list_for_tenant(self.tenant),
            lambda drawing: drawing.uploaded_by_user_id,
        )
        views = [assemble_quote_task_view(task, drawings) for task in tasks]
        if review_status is None:
            return views
        return [view for view in views if view.review_status is review_status]
