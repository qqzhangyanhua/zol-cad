from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from quote_assistant.adapter.db.models import (
    FactoryRow,
    PartDrawingEventRow,
    PartDrawingRow,
    QuoteSheetTemplateRow,
    QuoteTaskRow,
    UserRow,
)
from quote_assistant.adapter.security.passwords import hash_password
from quote_assistant.domain.entities import PartDrawingStatus, Role
from quote_assistant.domain.part_family import UNKNOWN_PART_FAMILY_ID


def create_factory(session: Session, name: str) -> UUID:
    row = FactoryRow(id=uuid4(), name=name, created_at=datetime.now(UTC))
    session.add(row)
    session.flush()
    return row.id


def create_quoter(session: Session, factory_id: UUID, username: str, password: str) -> UUID:
    return _create_user(session, factory_id, username, password, Role.QUOTER)


def create_admin(session: Session, factory_id: UUID, username: str, password: str) -> UUID:
    return _create_user(session, factory_id, username, password, Role.ADMIN)


def _create_user(
    session: Session, factory_id: UUID, username: str, password: str, role: Role
) -> UUID:
    row = UserRow(
        id=uuid4(),
        factory_id=factory_id,
        username=username,
        password_hash=hash_password(password),
        role=role.value,
        created_at=datetime.now(UTC),
    )
    session.add(row)
    session.flush()
    return row.id


def insert_part_drawing(
    session: Session,
    factory_id: UUID,
    filename: str,
    *,
    status: PartDrawingStatus = PartDrawingStatus.UPLOADED,
) -> UUID:
    drawing_id = uuid4()
    row = PartDrawingRow(
        id=drawing_id,
        factory_id=factory_id,
        original_filename=filename,
        uploaded_at=datetime.now(UTC),
        storage_key=f"part-drawings/{factory_id}/{drawing_id}/original.pdf",
        content_type="application/pdf",
        byte_size=0,
        page_count=1,
        selected_page=1,
        uploaded_by_user_id=None,
        status=status.value,
        quality_grade=None,
        is_assembly_or_exploded=False,
        low_quality_unreliable=False,
        extracted_fields=[],
        extraction_failure_reason=None,
        part_family_id=UNKNOWN_PART_FAMILY_ID,
        quote_task_id=None,
    )
    session.add(row)
    session.flush()
    return row.id


def insert_event(
    session: Session,
    *,
    drawing_id: UUID,
    factory_id: UUID,
    to_status: PartDrawingStatus,
    occurred_at: datetime,
    sequence_no: int,
    from_status: PartDrawingStatus | None = None,
) -> UUID:
    event_id = uuid4()
    session.add(
        PartDrawingEventRow(
            id=event_id,
            part_drawing_id=drawing_id,
            factory_id=factory_id,
            from_status=from_status.value if from_status else None,
            to_status=to_status.value,
            occurred_at=occurred_at,
            sequence_no=sequence_no,
            actor_user_id=None,
        )
    )
    session.flush()
    return event_id


def insert_quote_task(
    session: Session,
    factory_id: UUID,
    name: str,
    customer_name: str,
    created_by_user_id: UUID,
    *,
    created_at: datetime | None = None,
) -> UUID:
    row = QuoteTaskRow(
        id=uuid4(),
        factory_id=factory_id,
        name=name,
        customer_name=customer_name,
        created_at=created_at or datetime.now(UTC),
        created_by_user_id=created_by_user_id,
    )
    session.add(row)
    session.flush()
    return row.id


def insert_quote_sheet_template(
    session: Session,
    factory_id: UUID,
    columns: list[tuple[str, str]],
) -> None:
    """Onboarding-style write of a factory 报价底稿 template. No HTTP path."""
    session.add(
        QuoteSheetTemplateRow(
            factory_id=factory_id,
            columns=[{"source_key": source_key, "header": header} for source_key, header in columns],
        )
    )
    session.flush()


def login(client, username: str, password: str):
    return client.post("/auth/login", json={"username": username, "password": password})
