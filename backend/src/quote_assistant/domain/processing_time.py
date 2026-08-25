from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID, uuid4

from quote_assistant.domain.entities import (
    DrawingProcessingTime,
    ManualBaseline,
    PartDrawing,
    PartDrawingStatus,
    ProcessingTimeComparison,
)
from quote_assistant.domain.errors import InvalidManualBaseline
from quote_assistant.domain.part_drawing_state import PartDrawingEvent

MAX_PART_DESCRIPTION_LENGTH = 200
MAX_MANUAL_DURATION_SECONDS = 24 * 60 * 60


def new_manual_baseline(
    *,
    factory_id: UUID,
    part_description: str,
    manual_duration_seconds: int,
    recorded_at: datetime,
    recorded_by_user_id: UUID,
) -> ManualBaseline:
    description = part_description.strip()
    if not description:
        raise InvalidManualBaseline("请填写零件描述")
    if len(description) > MAX_PART_DESCRIPTION_LENGTH:
        raise InvalidManualBaseline(f"零件描述不能超过 {MAX_PART_DESCRIPTION_LENGTH} 字")
    if manual_duration_seconds <= 0:
        raise InvalidManualBaseline("人工耗时必须大于 0 秒")
    if manual_duration_seconds > MAX_MANUAL_DURATION_SECONDS:
        raise InvalidManualBaseline("人工耗时不能超过 24 小时")
    return ManualBaseline(
        id=uuid4(),
        factory_id=factory_id,
        part_description=description,
        manual_duration_seconds=manual_duration_seconds,
        recorded_at=recorded_at,
        recorded_by_user_id=recorded_by_user_id,
    )


def _first_occurred_at(
    events: Sequence[PartDrawingEvent],
    status: PartDrawingStatus,
) -> datetime | None:
    for event in events:
        if event.to_status is status:
            return event.occurred_at
    return None


def _seconds_between(start: datetime | None, end: datetime | None) -> float | None:
    if start is None or end is None:
        return None
    return (end - start).total_seconds()


def _mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def processing_time_from_events(
    drawing: PartDrawing,
    events: Sequence[PartDrawingEvent],
) -> DrawingProcessingTime | None:
    """处理耗时 = 已复核 − 上传。缺任一时间戳则排除（半成品不拉低数据）。"""
    owned = [event for event in events if event.part_drawing_id == drawing.id]
    uploaded_at = _first_occurred_at(owned, PartDrawingStatus.UPLOADED)
    reviewed_at = _first_occurred_at(owned, PartDrawingStatus.REVIEWED)
    if uploaded_at is None or reviewed_at is None:
        return None
    graded_at = _first_occurred_at(owned, PartDrawingStatus.GRADED)
    extracted_at = _first_occurred_at(owned, PartDrawingStatus.EXTRACTED)
    return DrawingProcessingTime(
        part_drawing_id=drawing.id,
        original_filename=drawing.original_filename,
        uploaded_at=uploaded_at,
        reviewed_at=reviewed_at,
        processing_seconds=(reviewed_at - uploaded_at).total_seconds(),
        grading_seconds=_seconds_between(uploaded_at, graded_at),
        extraction_seconds=_seconds_between(graded_at, extracted_at),
        review_seconds=_seconds_between(extracted_at, reviewed_at),
    )


def compare_processing_time(
    drawings: Sequence[PartDrawing],
    events: Sequence[PartDrawingEvent],
    baselines: Sequence[ManualBaseline],
) -> ProcessingTimeComparison:
    events_by_drawing: dict[UUID, list[PartDrawingEvent]] = {}
    for event in events:
        events_by_drawing.setdefault(event.part_drawing_id, []).append(event)

    items = [
        computed
        for drawing in drawings
        if (computed := processing_time_from_events(drawing, events_by_drawing.get(drawing.id, ())))
        is not None
    ]
    items.sort(key=lambda item: item.reviewed_at, reverse=True)

    ordered_baselines = sorted(baselines, key=lambda item: item.recorded_at, reverse=True)
    average_processing = _mean([item.processing_seconds for item in items])
    average_baseline = _mean([float(item.manual_duration_seconds) for item in ordered_baselines])
    saved = None
    if average_processing is not None and average_baseline is not None:
        saved = average_baseline - average_processing

    return ProcessingTimeComparison(
        reviewed_count=len(items),
        excluded_unreviewed_count=len(drawings) - len(items),
        average_processing_seconds=average_processing,
        average_grading_seconds=_mean(
            [item.grading_seconds for item in items if item.grading_seconds is not None]
        ),
        average_extraction_seconds=_mean(
            [item.extraction_seconds for item in items if item.extraction_seconds is not None]
        ),
        average_review_seconds=_mean(
            [item.review_seconds for item in items if item.review_seconds is not None]
        ),
        baseline_count=len(ordered_baselines),
        average_baseline_seconds=average_baseline,
        saved_seconds=saved,
        items=tuple(items),
        baselines=tuple(ordered_baselines),
    )
