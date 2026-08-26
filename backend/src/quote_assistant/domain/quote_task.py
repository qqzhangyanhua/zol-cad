from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from quote_assistant.domain.entities import PartDrawing, PartDrawingStatus
from quote_assistant.domain.errors import InvalidQuoteTask


class QuoteTaskReviewStatus(StrEnum):
    """Derived from member 零件图 复核 status. Not a stored 报价任务 state machine."""

    EMPTY = "无零件图"
    INCOMPLETE = "复核未完成"
    REVIEWED = "已复核"


QUOTE_TASK_REVIEW_STATUSES: tuple[QuoteTaskReviewStatus, ...] = tuple(QuoteTaskReviewStatus)

MAX_QUOTE_TASK_NAME_LENGTH = 200
MAX_CUSTOMER_NAME_LENGTH = 200


@dataclass(frozen=True)
class QuoteTask:
    """轻量归集层：把多张零件图归到一次询价。不含金额、不含审批、不含自身状态机。"""

    id: UUID
    factory_id: UUID
    name: str
    customer_name: str
    created_at: datetime
    created_by_user_id: UUID


@dataclass(frozen=True)
class QuoteTaskView:
    task: QuoteTask
    drawings: tuple[PartDrawing, ...]
    review_status: QuoteTaskReviewStatus
    unreviewed_member_count: int

    @property
    def drawing_count(self) -> int:
        return len(self.drawings)


def normalize_quote_task_text(value: str, *, field: str, max_length: int) -> str:
    stripped = value.strip()
    if not stripped:
        raise InvalidQuoteTask(f"请填写{field}")
    if len(stripped) > max_length:
        raise InvalidQuoteTask(f"{field}不能超过 {max_length} 个字")
    return stripped


def new_quote_task(
    *,
    factory_id: UUID,
    name: str,
    customer_name: str,
    created_at: datetime,
    created_by_user_id: UUID,
) -> QuoteTask:
    return QuoteTask(
        id=uuid4(),
        factory_id=factory_id,
        name=normalize_quote_task_text(
            name, field="任务名称", max_length=MAX_QUOTE_TASK_NAME_LENGTH
        ),
        customer_name=normalize_quote_task_text(
            customer_name, field="客户名称", max_length=MAX_CUSTOMER_NAME_LENGTH
        ),
        created_at=created_at,
        created_by_user_id=created_by_user_id,
    )


def derive_quote_task_review_status(drawings: Sequence[PartDrawing]) -> QuoteTaskReviewStatus:
    if not drawings:
        return QuoteTaskReviewStatus.EMPTY
    if all(drawing.status is PartDrawingStatus.REVIEWED for drawing in drawings):
        return QuoteTaskReviewStatus.REVIEWED
    return QuoteTaskReviewStatus.INCOMPLETE


def assemble_quote_task_view(
    task: QuoteTask,
    drawings: Sequence[PartDrawing],
    *,
    unreviewed_member_count: int | None = None,
) -> QuoteTaskView:
    members = tuple(drawing for drawing in drawings if drawing.quote_task_id == task.id)
    count = (
        unreviewed_member_count
        if unreviewed_member_count is not None
        else sum(1 for drawing in members if drawing.status is not PartDrawingStatus.REVIEWED)
    )
    return QuoteTaskView(
        task=task,
        drawings=members,
        review_status=derive_quote_task_review_status(members),
        unreviewed_member_count=count,
    )
