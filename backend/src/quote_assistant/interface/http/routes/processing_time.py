from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from quote_assistant.domain.errors import AdminRequired, InvalidManualBaseline
from quote_assistant.interface.http.deps import (
    get_compare_processing_time,
    get_record_manual_baseline,
)
from quote_assistant.interface.http.schemas import (
    ManualBaselineResponse,
    ProcessingTimeComparisonResponse,
    RecordManualBaselineRequest,
    to_manual_baseline_response,
    to_processing_time_comparison_response,
)
from quote_assistant.usecase.compare_processing_time import CompareProcessingTime
from quote_assistant.usecase.record_manual_baseline import RecordManualBaseline

router = APIRouter(tags=["processing-time"])


@router.get("/processing-time", response_model=ProcessingTimeComparisonResponse)
def get_processing_time(
    use_case: CompareProcessingTime = Depends(get_compare_processing_time),
) -> ProcessingTimeComparisonResponse:
    try:
        comparison = use_case.execute()
    except AdminRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return to_processing_time_comparison_response(comparison)


@router.post("/manual-baselines", response_model=ManualBaselineResponse)
def create_manual_baseline(
    payload: RecordManualBaselineRequest,
    use_case: RecordManualBaseline = Depends(get_record_manual_baseline),
) -> ManualBaselineResponse:
    try:
        baseline = use_case.execute(
            part_description=payload.part_description,
            manual_duration_seconds=payload.manual_duration_seconds,
        )
    except AdminRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InvalidManualBaseline as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return to_manual_baseline_response(baseline)
