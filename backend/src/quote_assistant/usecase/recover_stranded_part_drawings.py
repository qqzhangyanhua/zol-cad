from __future__ import annotations

from datetime import UTC, datetime

from quote_assistant.domain.entities import PartDrawingStatus
from quote_assistant.domain.part_drawing_state import record_transition
from quote_assistant.usecase.ports import (
    InFlightPartDrawingRepository,
    PartDrawingEventRepository,
    UnitOfWork,
)

STRANDED_REASON = "读图取数被中断（服务重启），请重试"

_IN_FLIGHT = frozenset(
    {
        PartDrawingStatus.UPLOADED,
        PartDrawingStatus.GRADING,
        PartDrawingStatus.EXTRACTING,
    }
)


class RecoverStrandedPartDrawings:
    """Startup sweep for a single-process deploy.

    MVP is pinned to one uvicorn worker / one replica (see docs/deploy.md). After
    that process starts, nothing else can still be running 分级 / 读图取数, so
    leftover 已上传 / 分级中 / 提取中 rows are stranded. Recovering them to
    提取失败 puts them back on the existing retry path.

    Do not run `uvicorn --workers N` or a second replica: that would mark another
    live process's in-flight 零件图 as failed. Multi-process recovery needs a
    lock / lease and is out of MVP scope.

    This is maintenance across every factory, not a 报价员 action, so it takes no
    Actor and uses the narrow cross-tenant port rather than widening the
    tenant-filtered one.
    """

    def __init__(
        self,
        drawings: InFlightPartDrawingRepository,
        events: PartDrawingEventRepository,
        uow: UnitOfWork,
    ) -> None:
        self._drawings = drawings
        self._events = events
        self._uow = uow

    def execute(self) -> int:
        recovered = 0
        for drawing in self._drawings.list_in_flight():
            if drawing.status not in _IN_FLIGHT:
                continue
            updated, event = record_transition(
                drawing,
                PartDrawingStatus.EXTRACT_FAILED,
                occurred_at=datetime.now(UTC),
                sequence_no=self._events.next_sequence(drawing.id),
                actor_user_id=None,
                extraction_failure_reason=STRANDED_REASON,
            )
            self._drawings.save(updated)
            self._events.add(event)
            recovered += 1
        if recovered:
            self._uow.commit()
        return recovered
