from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from quote_assistant.domain.entities import IncomingDrawing
from quote_assistant.domain.errors import (
    ExtractedFieldNotFound,
    IllegalPartDrawingTransition,
    IncompleteReview,
    PartDrawingNotFound,
)
from quote_assistant.interface.http.deps import (
    get_add_critical_dimension,
    get_complete_review,
    get_confirm_extracted_field,
    get_continue_despite_poor_quality,
    get_extract_part_drawing,
    get_get_part_drawing,
    get_ignore_extracted_field,
    get_issue_original_access_url,
    get_list_correction_records,
    get_list_part_drawing_events,
    get_list_part_drawings,
    get_reopen_review,
    get_unignore_extracted_field,
    get_update_extracted_field,
    get_upload_part_drawings,
)
from quote_assistant.interface.http.schemas import (
    AddCriticalDimensionRequest,
    CorrectionRecordListResponse,
    OriginalAccessResponse,
    PartDrawingEventListResponse,
    PartDrawingEventResponse,
    PartDrawingListResponse,
    PartDrawingResponse,
    RejectedUploadResponse,
    UpdateExtractedFieldRequest,
    UploadPartDrawingsResponse,
    to_correction_record_response,
    to_part_drawing_response,
)
from quote_assistant.usecase.continue_despite_poor_quality import ContinueDespitePoorQuality
from quote_assistant.usecase.extract_part_drawing import ExtractPartDrawing
from quote_assistant.usecase.get_part_drawing import GetPartDrawing
from quote_assistant.usecase.issue_original_access_url import IssueOriginalAccessUrl
from quote_assistant.usecase.list_correction_records import ListCorrectionRecords
from quote_assistant.usecase.list_part_drawing_events import ListPartDrawingEvents
from quote_assistant.usecase.list_part_drawings import ListPartDrawings
from quote_assistant.usecase.review_part_drawing import (
    AddCriticalDimension,
    CompleteReview,
    ConfirmExtractedField,
    IgnoreExtractedField,
    ReopenReview,
    UnignoreExtractedField,
    UpdateExtractedField,
)
from quote_assistant.usecase.upload_part_drawings import UploadPartDrawings

router = APIRouter(prefix="/part-drawings", tags=["part-drawings"])


def _parse_selected_pages(raw: str | None, file_count: int) -> list[int]:
    if not raw:
        return [1] * file_count
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="selected_pages 必须是页码数组") from exc
    if not isinstance(parsed, list) or not all(isinstance(item, int) for item in parsed):
        raise HTTPException(status_code=400, detail="selected_pages 必须是页码数组")
    if len(parsed) != file_count:
        raise HTTPException(status_code=400, detail="selected_pages 数量必须与文件数量一致")
    return parsed


@router.get("", response_model=PartDrawingListResponse)
def list_part_drawings(
    use_case: ListPartDrawings = Depends(get_list_part_drawings),
) -> PartDrawingListResponse:
    # factory_id query/body args are intentionally not accepted.
    items = use_case.execute()
    return PartDrawingListResponse(items=[to_part_drawing_response(item) for item in items])


@router.post("", response_model=UploadPartDrawingsResponse)
async def upload_part_drawings(
    files: list[UploadFile] = File(...),
    selected_pages: str | None = Form(default=None),
    use_case: UploadPartDrawings = Depends(get_upload_part_drawings),
) -> UploadPartDrawingsResponse:
    if not files:
        raise HTTPException(status_code=400, detail="请至少选择一张零件图")
    pages = _parse_selected_pages(selected_pages, len(files))
    incoming: list[IncomingDrawing] = []
    for upload, page in zip(files, pages, strict=True):
        content = await upload.read()
        incoming.append(
            IncomingDrawing(
                original_filename=upload.filename or "未命名文件",
                content=content,
                selected_page=page,
            )
        )
    result = use_case.execute(incoming)
    return UploadPartDrawingsResponse(
        items=[to_part_drawing_response(item) for item in result.items],
        rejected=[
            RejectedUploadResponse(
                original_filename=item.original_filename,
                detail=item.detail,
            )
            for item in result.rejected
        ],
    )


@router.get("/{drawing_id}", response_model=PartDrawingResponse)
def get_part_drawing(
    drawing_id: UUID,
    use_case: GetPartDrawing = Depends(get_get_part_drawing),
) -> PartDrawingResponse:
    try:
        drawing = use_case.execute(drawing_id)
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    return to_part_drawing_response(drawing)


@router.get("/{drawing_id}/correction-records", response_model=CorrectionRecordListResponse)
def list_correction_records(
    drawing_id: UUID,
    use_case: ListCorrectionRecords = Depends(get_list_correction_records),
) -> CorrectionRecordListResponse:
    try:
        records = use_case.execute(drawing_id)
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    return CorrectionRecordListResponse(
        items=[to_correction_record_response(record) for record in records]
    )


@router.get("/{drawing_id}/events", response_model=PartDrawingEventListResponse)
def list_part_drawing_events(
    drawing_id: UUID,
    use_case: ListPartDrawingEvents = Depends(get_list_part_drawing_events),
) -> PartDrawingEventListResponse:
    try:
        events = use_case.execute(drawing_id)
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    return PartDrawingEventListResponse(
        items=[
            PartDrawingEventResponse(
                id=event.id,
                from_status=event.from_status,
                to_status=event.to_status,
                occurred_at=event.occurred_at,
                sequence_no=event.sequence_no,
            )
            for event in events
        ]
    )


@router.post("/{drawing_id}/continue-despite-quality", response_model=PartDrawingResponse)
def continue_despite_poor_quality(
    drawing_id: UUID,
    use_case: ContinueDespitePoorQuality = Depends(get_continue_despite_poor_quality),
) -> PartDrawingResponse:
    try:
        drawing = use_case.execute(drawing_id)
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    except IllegalPartDrawingTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return to_part_drawing_response(drawing)


@router.post("/{drawing_id}/extract", response_model=PartDrawingResponse)
def extract_part_drawing(
    drawing_id: UUID,
    use_case: ExtractPartDrawing = Depends(get_extract_part_drawing),
) -> PartDrawingResponse:
    try:
        drawing = use_case.execute(drawing_id)
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    except IllegalPartDrawingTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return to_part_drawing_response(drawing)


@router.post("/{drawing_id}/fields/{field_key}/confirm", response_model=PartDrawingResponse)
def confirm_extracted_field(
    drawing_id: UUID,
    field_key: str,
    use_case: ConfirmExtractedField = Depends(get_confirm_extracted_field),
) -> PartDrawingResponse:
    try:
        drawing = use_case.execute(drawing_id, field_key)
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    except ExtractedFieldNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IllegalPartDrawingTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return to_part_drawing_response(drawing)


@router.patch("/{drawing_id}/fields/{field_key}", response_model=PartDrawingResponse)
def update_extracted_field(
    drawing_id: UUID,
    field_key: str,
    payload: UpdateExtractedFieldRequest,
    use_case: UpdateExtractedField = Depends(get_update_extracted_field),
) -> PartDrawingResponse:
    try:
        drawing = use_case.execute(drawing_id, field_key, payload.value)
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    except ExtractedFieldNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IllegalPartDrawingTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return to_part_drawing_response(drawing)


@router.post("/{drawing_id}/fields/{field_key}/ignore", response_model=PartDrawingResponse)
def ignore_extracted_field(
    drawing_id: UUID,
    field_key: str,
    use_case: IgnoreExtractedField = Depends(get_ignore_extracted_field),
) -> PartDrawingResponse:
    try:
        drawing = use_case.execute(drawing_id, field_key)
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    except ExtractedFieldNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IllegalPartDrawingTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return to_part_drawing_response(drawing)


@router.post("/{drawing_id}/fields/{field_key}/unignore", response_model=PartDrawingResponse)
def unignore_extracted_field(
    drawing_id: UUID,
    field_key: str,
    use_case: UnignoreExtractedField = Depends(get_unignore_extracted_field),
) -> PartDrawingResponse:
    try:
        drawing = use_case.execute(drawing_id, field_key)
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    except ExtractedFieldNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IllegalPartDrawingTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return to_part_drawing_response(drawing)


@router.post("/{drawing_id}/fields", response_model=PartDrawingResponse)
def add_critical_dimension(
    drawing_id: UUID,
    payload: AddCriticalDimensionRequest,
    use_case: AddCriticalDimension = Depends(get_add_critical_dimension),
) -> PartDrawingResponse:
    try:
        drawing = use_case.execute(drawing_id, payload.kind, payload.value, payload.label)
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    except ExtractedFieldNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IllegalPartDrawingTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return to_part_drawing_response(drawing)


@router.post("/{drawing_id}/reopen-review", response_model=PartDrawingResponse)
def reopen_review(
    drawing_id: UUID,
    use_case: ReopenReview = Depends(get_reopen_review),
) -> PartDrawingResponse:
    try:
        drawing = use_case.execute(drawing_id)
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    except IllegalPartDrawingTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return to_part_drawing_response(drawing)


@router.post("/{drawing_id}/complete-review", response_model=PartDrawingResponse)
def complete_review(
    drawing_id: UUID,
    use_case: CompleteReview = Depends(get_complete_review),
) -> PartDrawingResponse:
    try:
        drawing = use_case.execute(drawing_id)
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    except IncompleteReview as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except IllegalPartDrawingTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return to_part_drawing_response(drawing)


@router.get("/{drawing_id}/original", response_model=OriginalAccessResponse)
def get_part_drawing_original(
    drawing_id: UUID,
    use_case: IssueOriginalAccessUrl = Depends(get_issue_original_access_url),
) -> OriginalAccessResponse:
    try:
        access = use_case.execute(drawing_id)
    except PartDrawingNotFound as exc:
        raise HTTPException(status_code=404, detail="零件图不存在") from exc
    return OriginalAccessResponse(
        url=access.url,
        expires_at=access.expires_at,
        content_type=access.drawing.content_type,
        original_filename=access.drawing.original_filename,
        page_count=access.drawing.page_count,
        selected_page=access.drawing.selected_page,
    )
