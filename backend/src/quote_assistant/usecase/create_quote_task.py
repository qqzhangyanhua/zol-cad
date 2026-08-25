from __future__ import annotations

from datetime import UTC, datetime

from quote_assistant.domain.entities import Actor
from quote_assistant.domain.quote_task import QuoteTask, new_quote_task
from quote_assistant.usecase.ports import QuoteTaskRepository, UnitOfWork
from quote_assistant.usecase.tenant import TenantBoundUseCase


class CreateQuoteTask(TenantBoundUseCase):
    """Create a 报价任务 for the authenticated 报价员's factory."""

    def __init__(
        self,
        actor: Actor,
        quote_tasks: QuoteTaskRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._quote_tasks = quote_tasks
        self._uow = uow

    def execute(self, name: str, customer_name: str) -> QuoteTask:
        task = new_quote_task(
            factory_id=self.tenant.factory_id,
            name=name,
            customer_name=customer_name,
            created_at=datetime.now(UTC),
            created_by_user_id=self.actor.user_id,
        )
        self._quote_tasks.add(task)
        self._uow.commit()
        return task
