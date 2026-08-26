from __future__ import annotations

from datetime import UTC, date, datetime, time
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from quote_assistant.domain.errors import (
    IncompleteQuoteTaskReview,
    InvalidQuoteSheetTemplate,
    InvalidQuoteTask,
    PartDrawingNotFound,
    QuoteTaskNotFound,
)
from quote_assistant.domain.factory_preferences import FactoryPreferences
from quote_assistant.domain.quote_sheet import QuoteSheetFileFormat
from quote_assistant.domain.quote_task import QuoteTaskReviewStatus
from quote_assistant.interface.http.deps import (
    get_assign_part_drawing_to_quote_task,
    get_create_quote_task,
    get_export_quote_sheet,
    get_get_quote_task,
    get_list_quote_tasks,
    get_loaded_factory_preferences,
    get_remove_part_drawing_from_quote_task,
)
from quote_assistant.interface.http.schemas import (
    AssignPartDrawingRequest,
    CreateQuoteTaskRequest,
    QuoteTaskDetailResponse,
    QuoteTaskListResponse,
    to_quote_task_detail_response,
    to_quote_task_summary_response,
)
from quote_assistant.usecase.assign_part_drawing_to_quote_task import (
    AssignPartDrawingToQuoteTask,
    RemovePartDrawingFromQuoteTask,
)
from quote_assistant.usecase.create_quote_task import CreateQuoteTask
from quote_assistant.usecase.export_quote_sheet import ExportQuoteSheet
from quote_assistant.usecase.get_quote_task import GetQuoteTask
from quote_assistant.usecase.list_quote_tasks import ListQuoteTasks

router = APIRouter(prefix="/quote-tasks", tags=["quote-tasks"])


def _as_utc_bound(value: datetime | date, *, end: bool) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    bound = time.max if end else time.min
    return datetime.combine(value, bound, tzinfo=UTC)


def _parse_time_bound(raw: str | None, *, end: bool) -> datetime | None:
    if raw is None or raw.strip() == "":
        return None
    try:
        if len(raw) == 10:
            return _as_utc_bound(date.fromisoformat(raw), end=end)
        return _as_utc_bound(datetime.fromisoformat(raw.replace("Z", "+00:00")), end=False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="时间格式不正确") from exc


@router.post("", response_model=QuoteTaskDetailResponse)
def create_quote_task(
    payload: CreateQuoteTaskRequest,
    use_case: CreateQuoteTask = Depends(get_create_quote_task),
    get_use_case: GetQuoteTask = Depends(get_get_quote_task),
    prefs: FactoryPreferences = Depends(get_loaded_factory_preferences),
) -> QuoteTaskDetailResponse:
    try:
        task = use_case.execute(payload.name, payload.customer_name)
        view = get_use_case.execute(task.id)
    except InvalidQuoteTask as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return to_quote_task_detail_response(view, risk_label_priority=prefs.risk_label_priority)


@router.get("", response_model=QuoteTaskListResponse)
def list_quote_tasks(
    customer_name: str | None = Query(default=None),
    created_from: str | None = Query(default=None),
    created_to: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    use_case: ListQuoteTasks = Depends(get_list_quote_tasks),
) -> QuoteTaskListResponse:
    # factory_id query args are intentionally not accepted.
    parsed_status: QuoteTaskReviewStatus | None = None
    if review_status:
        try:
            parsed_status = QuoteTaskReviewStatus(review_status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="状态不正确") from exc
    views = use_case.execute(
        customer_name=customer_name,
        created_from=_parse_time_bound(created_from, end=False),
        created_to=_parse_time_bound(created_to, end=True),
        review_status=parsed_status,
    )
    return QuoteTaskListResponse(items=[to_quote_task_summary_response(view) for view in views])


@router.get("/{quote_task_id}", response_model=QuoteTaskDetailResponse)
def get_quote_task(
    quote_task_id: UUID,
    use_case: GetQuoteTask = Depends(get_get_quote_task),
    prefs: FactoryPreferences = Depends(get_loaded_factory_preferences),
) -> QuoteTaskDetailResponse:
    try:
        view = use_case.execute(quote_task_id)
    except QuoteTaskNotFound as exc:
        raise HTTPException(status_code=404, detail="报价任务不存在") from exc
    return to_quote_task_detail_response(view, risk_label_priority=prefs.risk_label_priority)


@router.post("/{quote_task_id}/part-drawings", response_model=QuoteTaskDetailResponse)
def assign_part_drawing(
    quote_task_id: UUID,
    payload: AssignPartDrawingRequest,
    assign: AssignPartDrawingToQuoteTask = Depends(get_assign_part_drawing_to_quote_task),
    get_use_case: GetQuoteTask = Depends(get_get_quote_task),
    prefs: FactoryPreferences = Depends(get_loaded_factory_preferences),
) -> QuoteTaskDetailResponse:
    try:
        assign.execute(payload.part_drawing_id, quote_task_id)
        view = get_use_case.execute(quote_task_id)
    except QuoteTaskNotFound as exc:
        raise HTTPException(status_code=404, detail="报价任务不存在") from exc
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    return to_quote_task_detail_response(view, risk_label_priority=prefs.risk_label_priority)


@router.delete("/{quote_task_id}/part-drawings/{drawing_id}", response_model=QuoteTaskDetailResponse)
def remove_part_drawing(
    quote_task_id: UUID,
    drawing_id: UUID,
    use_case: RemovePartDrawingFromQuoteTask = Depends(get_remove_part_drawing_from_quote_task),
    get_use_case: GetQuoteTask = Depends(get_get_quote_task),
    prefs: FactoryPreferences = Depends(get_loaded_factory_preferences),
) -> QuoteTaskDetailResponse:
    try:
        use_case.execute(quote_task_id, drawing_id)
        view = get_use_case.execute(quote_task_id)
    except QuoteTaskNotFound as exc:
        raise HTTPException(status_code=404, detail="报价任务不存在") from exc
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    return to_quote_task_detail_response(view, risk_label_priority=prefs.risk_label_priority)


@router.get("/{quote_task_id}/quote-sheet")
def export_quote_sheet(
    quote_task_id: UUID,
    file_format: str = Query(default="xlsx", alias="format"),
    use_case: ExportQuoteSheet = Depends(get_export_quote_sheet),
) -> Response:
    try:
        resolved_format = QuoteSheetFileFormat(file_format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="导出格式只支持 xlsx 或 csv") from exc
    try:
        sheet = use_case.execute(quote_task_id, resolved_format)
    except QuoteTaskNotFound as exc:
        raise HTTPException(status_code=404, detail="报价任务不存在") from exc
    except IncompleteQuoteTaskReview as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InvalidQuoteSheetTemplate as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    encoded = quote(sheet.filename)
    return Response(
        content=sheet.content,
        media_type=sheet.media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )
