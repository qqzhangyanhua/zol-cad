from __future__ import annotations

from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from quote_assistant.adapter.db.models import (
    CorrectionRecordRow,
    ManualBaselineRow,
    PartDrawingEventRow,
    PartDrawingRow,
    QuoteTaskRow,
    SessionRow,
    UserRow,
)
from quote_assistant.adapter.security.passwords import verify_password
from quote_assistant.domain.correction import CorrectionRecord
from quote_assistant.domain.entities import (
    IssuedSession,
    ManualBaseline,
    PartDrawing,
    PartDrawingStatus,
    Role,
    User,
)
from quote_assistant.domain.extraction import ExtractedField, FieldCategory, FieldSource
from quote_assistant.domain.part_drawing_state import PartDrawingEvent
from quote_assistant.domain.quality import QualityGrade
from quote_assistant.domain.quote_task import QuoteTask
from quote_assistant.usecase.tenant import TenantScope


def _fields_to_json(fields: tuple[ExtractedField, ...]) -> list[dict[str, object]]:
    return [
        {
            "key": field.key,
            "label": field.label,
            "value": field.value,
            "category": field.category.value,
            "confirmed": field.confirmed,
            "ignored": field.ignored,
            "source": field.source.value,
        }
        for field in fields
    ]


def _field_source(raw: object) -> FieldSource:
    try:
        return FieldSource(str(raw))
    except ValueError:
        return FieldSource.EXTRACTED


def _fields_from_json(raw: list[dict[str, object]] | None) -> tuple[ExtractedField, ...]:
    if not raw:
        return ()
    parsed: list[ExtractedField] = []
    for item in raw:
        value = item.get("value")
        parsed.append(
            ExtractedField(
                key=str(item["key"]),
                label=str(item["label"]),
                value=value if isinstance(value, str) else None,
                category=FieldCategory(str(item["category"])),
                confirmed=bool(item.get("confirmed", False)),
                ignored=bool(item.get("ignored", False)),
                source=_field_source(item.get("source")),
            )
        )
    return tuple(parsed)


def _to_part_drawing(row: PartDrawingRow) -> PartDrawing:
    return PartDrawing(
        id=row.id,
        factory_id=row.factory_id,
        original_filename=row.original_filename,
        uploaded_at=row.uploaded_at,
        storage_key=row.storage_key,
        content_type=row.content_type,
        byte_size=row.byte_size,
        page_count=row.page_count,
        selected_page=row.selected_page,
        uploaded_by_user_id=row.uploaded_by_user_id,
        status=PartDrawingStatus(row.status),
        quality_grade=QualityGrade(row.quality_grade) if row.quality_grade else None,
        is_assembly_or_exploded=row.is_assembly_or_exploded,
        low_quality_unreliable=row.low_quality_unreliable,
        extracted_fields=_fields_from_json(row.extracted_fields),
        extraction_failure_reason=row.extraction_failure_reason,
        part_family_id=row.part_family_id,
        quote_task_id=row.quote_task_id,
    )


def _to_event(row: PartDrawingEventRow) -> PartDrawingEvent:
    occurred_at = row.occurred_at
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=UTC)
    return PartDrawingEvent(
        id=row.id,
        part_drawing_id=row.part_drawing_id,
        factory_id=row.factory_id,
        from_status=PartDrawingStatus(row.from_status) if row.from_status else None,
        to_status=PartDrawingStatus(row.to_status),
        occurred_at=occurred_at,
        sequence_no=row.sequence_no,
        actor_user_id=row.actor_user_id,
    )


def _to_user(row: UserRow) -> User:
    return User(
        id=row.id,
        factory_id=row.factory_id,
        factory_name=row.factory.name,
        username=row.username,
        role=Role(row.role),
    )


class SqlUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID) -> User | None:
        row = self._session.execute(
            select(UserRow).options(joinedload(UserRow.factory)).where(UserRow.id == user_id)
        ).unique().scalar_one_or_none()
        if row is None:
            return None
        return _to_user(row)

    def get_by_username(self, username: str) -> User | None:
        row = self._session.execute(
            select(UserRow)
            .options(joinedload(UserRow.factory))
            .where(UserRow.username == username)
        ).unique().scalar_one_or_none()
        if row is None:
            return None
        return _to_user(row)


class SqlPasswordAuthenticator:
    def __init__(self, session: Session) -> None:
        self._session = session

    def authenticate(self, username: str, password: str) -> User | None:
        row = self._session.execute(
            select(UserRow)
            .options(joinedload(UserRow.factory))
            .where(UserRow.username == username)
        ).unique().scalar_one_or_none()
        if row is None:
            return None
        if not verify_password(password, row.password_hash):
            return None
        return _to_user(row)


class SqlSessionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, user_id: UUID, ttl: timedelta) -> IssuedSession:
        now = datetime.now(UTC)
        issued = IssuedSession(
            token=token_urlsafe(32),
            user_id=user_id,
            expires_at=now + ttl,
        )
        self._session.add(
            SessionRow(
                token=issued.token,
                user_id=issued.user_id,
                expires_at=issued.expires_at,
                created_at=now,
            )
        )
        return issued

    def get_valid(self, token: str) -> IssuedSession | None:
        row = self._session.execute(
            select(SessionRow).where(SessionRow.token == token)
        ).scalar_one_or_none()
        if row is None:
            return None
        expires_at = row.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= datetime.now(UTC):
            return None
        return IssuedSession(token=row.token, user_id=row.user_id, expires_at=expires_at)

    def revoke(self, token: str) -> None:
        row = self._session.execute(
            select(SessionRow).where(SessionRow.token == token)
        ).scalar_one_or_none()
        if row is not None:
            self._session.delete(row)


class SqlPartDrawingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_tenant(self, tenant: TenantScope) -> list[PartDrawing]:
        rows = self._session.execute(
            select(PartDrawingRow)
            .where(PartDrawingRow.factory_id == tenant.factory_id)
            .order_by(PartDrawingRow.uploaded_at.desc())
        ).scalars()
        return [_to_part_drawing(row) for row in rows]

    def get_for_tenant(self, tenant: TenantScope, drawing_id: UUID) -> PartDrawing | None:
        row = self._session.execute(
            select(PartDrawingRow).where(
                PartDrawingRow.id == drawing_id,
                PartDrawingRow.factory_id == tenant.factory_id,
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return _to_part_drawing(row)

    def list_for_quote_task(self, tenant: TenantScope, quote_task_id: UUID) -> list[PartDrawing]:
        rows = self._session.execute(
            select(PartDrawingRow)
            .where(
                PartDrawingRow.factory_id == tenant.factory_id,
                PartDrawingRow.quote_task_id == quote_task_id,
            )
            .order_by(PartDrawingRow.uploaded_at.asc())
        ).scalars()
        return [_to_part_drawing(row) for row in rows]

    def add(self, drawing: PartDrawing) -> None:
        self._session.add(
            PartDrawingRow(
                id=drawing.id,
                factory_id=drawing.factory_id,
                original_filename=drawing.original_filename,
                uploaded_at=drawing.uploaded_at,
                storage_key=drawing.storage_key,
                content_type=drawing.content_type,
                byte_size=drawing.byte_size,
                page_count=drawing.page_count,
                selected_page=drawing.selected_page,
                uploaded_by_user_id=drawing.uploaded_by_user_id,
                status=drawing.status.value,
                quality_grade=drawing.quality_grade.value if drawing.quality_grade else None,
                is_assembly_or_exploded=drawing.is_assembly_or_exploded,
                low_quality_unreliable=drawing.low_quality_unreliable,
                extracted_fields=_fields_to_json(drawing.extracted_fields),
                extraction_failure_reason=drawing.extraction_failure_reason,
                part_family_id=drawing.part_family_id,
                quote_task_id=drawing.quote_task_id,
            )
        )
        self._session.flush()

    def save(self, drawing: PartDrawing) -> None:
        row = self._session.get(PartDrawingRow, drawing.id)
        if row is None:
            self.add(drawing)
            return
        row.original_filename = drawing.original_filename
        row.storage_key = drawing.storage_key
        row.content_type = drawing.content_type
        row.byte_size = drawing.byte_size
        row.page_count = drawing.page_count
        row.selected_page = drawing.selected_page
        row.uploaded_by_user_id = drawing.uploaded_by_user_id
        row.status = drawing.status.value
        row.quality_grade = drawing.quality_grade.value if drawing.quality_grade else None
        row.is_assembly_or_exploded = drawing.is_assembly_or_exploded
        row.low_quality_unreliable = drawing.low_quality_unreliable
        row.extracted_fields = _fields_to_json(drawing.extracted_fields)
        row.extraction_failure_reason = drawing.extraction_failure_reason
        row.part_family_id = drawing.part_family_id
        row.quote_task_id = drawing.quote_task_id


class SqlPartDrawingEventRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, event: PartDrawingEvent) -> None:
        self._session.add(
            PartDrawingEventRow(
                id=event.id,
                part_drawing_id=event.part_drawing_id,
                factory_id=event.factory_id,
                from_status=event.from_status.value if event.from_status else None,
                to_status=event.to_status.value,
                occurred_at=event.occurred_at,
                sequence_no=event.sequence_no,
                actor_user_id=event.actor_user_id,
            )
        )
        self._session.flush()

    def list_for_drawing(self, tenant: TenantScope, drawing_id: UUID) -> list[PartDrawingEvent]:
        rows = self._session.execute(
            select(PartDrawingEventRow)
            .where(
                PartDrawingEventRow.part_drawing_id == drawing_id,
                PartDrawingEventRow.factory_id == tenant.factory_id,
            )
            .order_by(PartDrawingEventRow.sequence_no.asc())
        ).scalars()
        return [_to_event(row) for row in rows]

    def next_sequence(self, drawing_id: UUID) -> int:
        self._session.flush()
        current = self._session.execute(
            select(func.coalesce(func.max(PartDrawingEventRow.sequence_no), 0)).where(
                PartDrawingEventRow.part_drawing_id == drawing_id
            )
        ).scalar_one()
        return int(current) + 1

    def list_for_tenant(self, tenant: TenantScope) -> list[PartDrawingEvent]:
        rows = self._session.execute(
            select(PartDrawingEventRow)
            .where(PartDrawingEventRow.factory_id == tenant.factory_id)
            .order_by(PartDrawingEventRow.occurred_at.asc(), PartDrawingEventRow.sequence_no.asc())
        ).scalars()
        return [_to_event(row) for row in rows]


def _to_correction(row: CorrectionRecordRow) -> CorrectionRecord:
    occurred_at = row.occurred_at
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=UTC)
    return CorrectionRecord(
        id=row.id,
        factory_id=row.factory_id,
        part_drawing_id=row.part_drawing_id,
        field_key=row.field_key,
        field_type=row.field_type,
        old_value=row.old_value,
        new_value=row.new_value,
        actor_user_id=row.actor_user_id,
        occurred_at=occurred_at,
    )


class SqlCorrectionRecordRepository:
    """Append-only. There is no update or overwrite path."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: CorrectionRecord) -> None:
        self._session.add(
            CorrectionRecordRow(
                id=record.id,
                factory_id=record.factory_id,
                part_drawing_id=record.part_drawing_id,
                field_key=record.field_key,
                field_type=record.field_type,
                old_value=record.old_value,
                new_value=record.new_value,
                actor_user_id=record.actor_user_id,
                occurred_at=record.occurred_at,
            )
        )
        self._session.flush()

    def list_for_drawing(self, tenant: TenantScope, drawing_id: UUID) -> list[CorrectionRecord]:
        rows = self._session.execute(
            select(CorrectionRecordRow)
            .where(
                CorrectionRecordRow.part_drawing_id == drawing_id,
                CorrectionRecordRow.factory_id == tenant.factory_id,
            )
            .order_by(CorrectionRecordRow.occurred_at.asc(), CorrectionRecordRow.id.asc())
        ).scalars()
        return [_to_correction(row) for row in rows]

    def list_for_tenant(self, tenant: TenantScope) -> list[CorrectionRecord]:
        rows = self._session.execute(
            select(CorrectionRecordRow)
            .where(CorrectionRecordRow.factory_id == tenant.factory_id)
            .order_by(CorrectionRecordRow.occurred_at.asc(), CorrectionRecordRow.id.asc())
        ).scalars()
        return [_to_correction(row) for row in rows]


def _to_manual_baseline(row: ManualBaselineRow) -> ManualBaseline:
    recorded_at = row.recorded_at
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=UTC)
    return ManualBaseline(
        id=row.id,
        factory_id=row.factory_id,
        part_description=row.part_description,
        manual_duration_seconds=row.manual_duration_seconds,
        recorded_at=recorded_at,
        recorded_by_user_id=row.recorded_by_user_id,
    )


class SqlManualBaselineRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, baseline: ManualBaseline) -> None:
        self._session.add(
            ManualBaselineRow(
                id=baseline.id,
                factory_id=baseline.factory_id,
                part_description=baseline.part_description,
                manual_duration_seconds=baseline.manual_duration_seconds,
                recorded_at=baseline.recorded_at,
                recorded_by_user_id=baseline.recorded_by_user_id,
            )
        )
        self._session.flush()

    def list_for_tenant(self, tenant: TenantScope) -> list[ManualBaseline]:
        rows = self._session.execute(
            select(ManualBaselineRow)
            .where(ManualBaselineRow.factory_id == tenant.factory_id)
            .order_by(ManualBaselineRow.recorded_at.desc())
        ).scalars()
        return [_to_manual_baseline(row) for row in rows]


def _to_quote_task(row: QuoteTaskRow) -> QuoteTask:
    created_at = row.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return QuoteTask(
        id=row.id,
        factory_id=row.factory_id,
        name=row.name,
        customer_name=row.customer_name,
        created_at=created_at,
        created_by_user_id=row.created_by_user_id,
    )


class SqlQuoteTaskRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, task: QuoteTask) -> None:
        self._session.add(
            QuoteTaskRow(
                id=task.id,
                factory_id=task.factory_id,
                name=task.name,
                customer_name=task.customer_name,
                created_at=task.created_at,
                created_by_user_id=task.created_by_user_id,
            )
        )
        self._session.flush()

    def get_for_tenant(self, tenant: TenantScope, task_id: UUID) -> QuoteTask | None:
        row = self._session.execute(
            select(QuoteTaskRow).where(
                QuoteTaskRow.id == task_id,
                QuoteTaskRow.factory_id == tenant.factory_id,
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return _to_quote_task(row)

    def list_for_tenant(
        self,
        tenant: TenantScope,
        *,
        customer_name: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> list[QuoteTask]:
        stmt = select(QuoteTaskRow).where(QuoteTaskRow.factory_id == tenant.factory_id)
        if customer_name:
            stmt = stmt.where(QuoteTaskRow.customer_name.ilike(f"%{customer_name}%"))
        if created_from is not None:
            stmt = stmt.where(QuoteTaskRow.created_at >= created_from)
        if created_to is not None:
            stmt = stmt.where(QuoteTaskRow.created_at <= created_to)
        rows = self._session.execute(stmt.order_by(QuoteTaskRow.created_at.desc())).scalars()
        return [_to_quote_task(row) for row in rows]
