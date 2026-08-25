from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from quote_assistant.domain.correction import records_for_value_changes
from quote_assistant.domain.entities import Actor, PartDrawing
from quote_assistant.domain.review import (
    add_critical_dimension,
    begin_reviewing,
    complete_review,
    confirm_extracted_field,
    edit_extracted_field,
    ignore_extracted_field,
    reopen_review,
    unignore_extracted_field,
)
from quote_assistant.usecase.ports import (
    CorrectionRecordRepository,
    PartDrawingEventRepository,
    PartDrawingRepository,
    UnitOfWork,
)
from quote_assistant.usecase.tenant import (
    TenantBoundUseCase,
    TenantScope,
    require_visible_drawing,
)


def _load_for_tenant(
    actor: Actor,
    drawings: PartDrawingRepository,
    tenant: TenantScope,
    drawing_id: UUID,
) -> PartDrawing:
    return require_visible_drawing(actor, drawings.get_for_tenant(tenant, drawing_id))


def _save_review_action(
    mutated: PartDrawing,
    *,
    actor_user_id: UUID,
    drawings: PartDrawingRepository,
    events: PartDrawingEventRepository,
) -> PartDrawing:
    drawing, started = begin_reviewing(
        mutated,
        occurred_at=datetime.now(UTC),
        sequence_no=events.next_sequence(mutated.id),
        actor_user_id=actor_user_id,
    )
    drawings.save(drawing)
    if started is not None:
        events.add(started)
    return drawing


class ConfirmExtractedField(TenantBoundUseCase):
    """报价员逐项点击确认。"""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events
        self._uow = uow

    def execute(self, drawing_id: UUID, field_key: str) -> PartDrawing:
        drawing = _load_for_tenant(self.actor, self._drawings, self.tenant, drawing_id)
        drawing = _save_review_action(
            confirm_extracted_field(drawing, field_key),
            actor_user_id=self.actor.user_id,
            drawings=self._drawings,
            events=self._events,
        )
        self._uow.commit()
        return drawing


class UpdateExtractedField(TenantBoundUseCase):
    """报价员就地修改提取值；修改立即落库，并追加一条不可变修正记录。"""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
        corrections: CorrectionRecordRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events
        self._corrections = corrections
        self._uow = uow

    def execute(self, drawing_id: UUID, field_key: str, value: str | None) -> PartDrawing:
        drawing = _load_for_tenant(self.actor, self._drawings, self.tenant, drawing_id)
        before = drawing
        drawing = _save_review_action(
            edit_extracted_field(drawing, field_key, value),
            actor_user_id=self.actor.user_id,
            drawings=self._drawings,
            events=self._events,
        )
        occurred_at = datetime.now(UTC)
        for record in records_for_value_changes(
            before,
            drawing,
            actor_user_id=self.actor.user_id,
            occurred_at=occurred_at,
        ):
            self._corrections.add(record)
        self._uow.commit()
        return drawing


class IgnoreExtractedField(TenantBoundUseCase):
    """报价员把不适用项标为忽略；忽略项不阻塞已复核。"""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events
        self._uow = uow

    def execute(self, drawing_id: UUID, field_key: str) -> PartDrawing:
        drawing = _load_for_tenant(self.actor, self._drawings, self.tenant, drawing_id)
        drawing = _save_review_action(
            ignore_extracted_field(drawing, field_key),
            actor_user_id=self.actor.user_id,
            drawings=self._drawings,
            events=self._events,
        )
        self._uow.commit()
        return drawing


class UnignoreExtractedField(TenantBoundUseCase):
    """撤销忽略，使该项重新参与需确认判定与风险标签。"""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events
        self._uow = uow

    def execute(self, drawing_id: UUID, field_key: str) -> PartDrawing:
        drawing = _load_for_tenant(self.actor, self._drawings, self.tenant, drawing_id)
        drawing = _save_review_action(
            unignore_extracted_field(drawing, field_key),
            actor_user_id=self.actor.user_id,
            drawings=self._drawings,
            events=self._events,
        )
        self._uow.commit()
        return drawing


class AddCriticalDimension(TenantBoundUseCase):
    """手工补录一条 AI 未提出的关键尺寸，并留下原值为空的修正记录。"""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
        corrections: CorrectionRecordRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events
        self._corrections = corrections
        self._uow = uow

    def execute(
        self,
        drawing_id: UUID,
        kind: str,
        value: str,
        label: str | None = None,
    ) -> PartDrawing:
        drawing = _load_for_tenant(self.actor, self._drawings, self.tenant, drawing_id)
        before = drawing
        drawing = _save_review_action(
            add_critical_dimension(drawing, kind, value, label),
            actor_user_id=self.actor.user_id,
            drawings=self._drawings,
            events=self._events,
        )
        occurred_at = datetime.now(UTC)
        for record in records_for_value_changes(
            before,
            drawing,
            actor_user_id=self.actor.user_id,
            occurred_at=occurred_at,
        ):
            self._corrections.add(record)
        self._uow.commit()
        return drawing


class ReopenReview(TenantBoundUseCase):
    """已复核的零件图重新打开，改动保留。"""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events
        self._uow = uow

    def execute(self, drawing_id: UUID) -> PartDrawing:
        drawing = _load_for_tenant(self.actor, self._drawings, self.tenant, drawing_id)
        drawing, event = reopen_review(
            drawing,
            occurred_at=datetime.now(UTC),
            sequence_no=self._events.next_sequence(drawing.id),
            actor_user_id=self.actor.user_id,
        )
        self._drawings.save(drawing)
        self._events.add(event)
        self._uow.commit()
        return drawing


class CompleteReview(TenantBoundUseCase):
    """全部需确认项处理完后，把零件图标记为已复核。"""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events
        self._uow = uow

    def execute(self, drawing_id: UUID) -> PartDrawing:
        drawing = _load_for_tenant(self.actor, self._drawings, self.tenant, drawing_id)
        drawing, event = complete_review(
            drawing,
            occurred_at=datetime.now(UTC),
            sequence_no=self._events.next_sequence(drawing.id),
            actor_user_id=self.actor.user_id,
        )
        self._drawings.save(drawing)
        self._events.add(event)
        self._uow.commit()
        return drawing
