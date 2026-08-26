from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from quote_assistant.domain.entities import Actor, PartDrawing, PartDrawingStatus
from quote_assistant.domain.errors import (
    ExtractionEngineFailed,
    ExtractionValidationFailed,
    IllegalPartDrawingTransition,
)
from quote_assistant.domain.part_drawing_state import record_transition, status_after_grade
from quote_assistant.usecase.extract_part_drawing import apply_extraction, build_extraction_request
from quote_assistant.usecase.ports import (
    DrawingPageRenderer,
    ExtractionEngine,
    ObjectStorage,
    PartDrawingEventRepository,
    PartDrawingRepository,
    UnitOfWork,
)
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_visible_drawing

_GRADABLE = frozenset({PartDrawingStatus.UPLOADED, PartDrawingStatus.EXTRACT_FAILED})
_GRADING_FAILURE_REASON = "图纸质量分级失败，请重试"


def apply_grading(
    drawing: PartDrawing,
    *,
    actor_user_id: UUID | None,
    drawings: PartDrawingRepository,
    events: PartDrawingEventRepository,
    storage: ObjectStorage,
    renderer: DrawingPageRenderer,
    engine: ExtractionEngine,
) -> PartDrawing:
    """分级中 → 已分级 / 建议人工 / 超出范围 / 提取失败. Caller owns the transaction."""
    if drawing.status not in _GRADABLE:
        raise IllegalPartDrawingTransition(
            f"零件图处于「{drawing.status.value}」，不能开始图纸质量分级"
        )

    drawing, started = record_transition(
        drawing,
        PartDrawingStatus.GRADING,
        occurred_at=datetime.now(UTC),
        sequence_no=events.next_sequence(drawing.id),
        actor_user_id=actor_user_id,
        extraction_failure_reason=None,
    )
    drawings.save(drawing)
    events.add(started)

    try:
        result = engine.extract(build_extraction_request(drawing, storage=storage, renderer=renderer))
    except (ExtractionValidationFailed, ExtractionEngineFailed) as exc:
        drawing, finished = _grading_failed(drawing, events, actor_user_id, str(exc))
    except Exception:
        drawing, finished = _grading_failed(drawing, events, actor_user_id, _GRADING_FAILURE_REASON)
    else:
        drawing, finished = record_transition(
            drawing,
            status_after_grade(result),
            occurred_at=datetime.now(UTC),
            sequence_no=events.next_sequence(drawing.id),
            actor_user_id=actor_user_id,
            quality_grade=result.quality_grade,
            is_assembly_or_exploded=result.is_assembly_or_exploded,
        )
    drawings.save(drawing)
    events.add(finished)
    return drawing


def _grading_failed(
    drawing: PartDrawing,
    events: PartDrawingEventRepository,
    actor_user_id: UUID | None,
    reason: str,
):
    return record_transition(
        drawing,
        PartDrawingStatus.EXTRACT_FAILED,
        occurred_at=datetime.now(UTC),
        sequence_no=events.next_sequence(drawing.id),
        actor_user_id=actor_user_id,
        extraction_failure_reason=reason,
    )


class ProcessPartDrawing(TenantBoundUseCase):
    """Advance one stored 零件图 as far as it should go: 分级 first if it never was, then 读图取数.

    Serves both the post-upload background job and the 报价员's 重试 button, so a drawing
    whose 分级 itself failed retries from 分级 instead of skipping straight to 读图取数
    with no 图纸质量分级 — that would let a 差图 slip past the 劝退 branch.

    Runs on behalf of the uploading 报价员, so tenant filtering and the event audit trail
    stay identical to the synchronous path. 分级 commits before 读图取数 starts, otherwise
    the 报价员 would sit on 分级中 until the whole pipeline finished.
    """

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
        storage: ObjectStorage,
        renderer: DrawingPageRenderer,
        engine: ExtractionEngine,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events
        self._storage = storage
        self._renderer = renderer
        self._engine = engine
        self._uow = uow

    def execute(self, drawing_id: UUID) -> PartDrawing:
        drawing = require_visible_drawing(
            self.actor, self._drawings.get_for_tenant(self.tenant, drawing_id)
        )
        if drawing.quality_grade is None:
            drawing = apply_grading(
                drawing,
                actor_user_id=self.actor.user_id,
                drawings=self._drawings,
                events=self._events,
                storage=self._storage,
                renderer=self._renderer,
                engine=self._engine,
            )
            self._uow.commit()
            if drawing.status is not PartDrawingStatus.GRADED:
                return drawing
        drawing = apply_extraction(
            drawing,
            actor_user_id=self.actor.user_id,
            drawings=self._drawings,
            events=self._events,
            storage=self._storage,
            renderer=self._renderer,
            engine=self._engine,
        )
        self._uow.commit()
        return drawing
