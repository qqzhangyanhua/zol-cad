from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from quote_assistant.domain.errors import AdminRequired
from quote_assistant.interface.http.deps import get_list_correction_stats
from quote_assistant.interface.http.schemas import (
    CorrectionStatsResponse,
    to_correction_stat_response,
)
from quote_assistant.usecase.list_correction_stats import ListCorrectionStats

router = APIRouter(tags=["correction-stats"])


@router.get("/correction-stats", response_model=CorrectionStatsResponse)
def list_correction_stats(
    use_case: ListCorrectionStats = Depends(get_list_correction_stats),
) -> CorrectionStatsResponse:
    try:
        result = use_case.execute()
    except AdminRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return CorrectionStatsResponse(
        items=[to_correction_stat_response(item) for item in result.items],
        purpose=result.purpose,
    )
