from __future__ import annotations

from fastapi import APIRouter, Depends

from quote_assistant.interface.http.deps import get_list_part_drawings
from quote_assistant.interface.http.schemas import PartDrawingListResponse, PartDrawingResponse
from quote_assistant.usecase.list_part_drawings import ListPartDrawings

router = APIRouter(prefix="/part-drawings", tags=["part-drawings"])


@router.get("", response_model=PartDrawingListResponse)
def list_part_drawings(
    use_case: ListPartDrawings = Depends(get_list_part_drawings),
) -> PartDrawingListResponse:
    # factory_id query/body args are intentionally not accepted.
    items = use_case.execute()
    return PartDrawingListResponse(
        items=[
            PartDrawingResponse(
                id=item.id,
                original_filename=item.original_filename,
                uploaded_at=item.uploaded_at,
            )
            for item in items
        ]
    )
