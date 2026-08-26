from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from quote_assistant.adapter.db.models import FactoryRow, UserRow
from quote_assistant.adapter.security.passwords import hash_password
from quote_assistant.config import Settings
from quote_assistant.domain.entities import Role


def _ensure_factory(session: Session, name: str, now: datetime) -> UUID:
    existing = session.execute(
        select(FactoryRow).where(FactoryRow.name == name)
    ).scalar_one_or_none()
    if existing is not None:
        return existing.id
    row = FactoryRow(id=uuid4(), name=name, created_at=now)
    session.add(row)
    session.flush()
    return row.id


def _ensure_user(
    session: Session,
    *,
    factory_id: UUID,
    username: str,
    password: str,
    role: Role,
    now: datetime,
) -> None:
    existing = session.execute(
        select(UserRow).where(UserRow.username == username)
    ).scalar_one_or_none()
    if existing is not None:
        return
    session.add(
        UserRow(
            id=uuid4(),
            factory_id=factory_id,
            username=username,
            password_hash=hash_password(password),
            role=role.value,
            created_at=now,
        )
    )


def seed_demo_data(session_factory: sessionmaker[Session], settings: Settings) -> None:
    session = session_factory()
    try:
        now = datetime.now(UTC)
        factory_a = _ensure_factory(session, "华东精密", now)
        factory_b = _ensure_factory(session, "南方模具", now)
        _ensure_user(
            session,
            factory_id=factory_a,
            username="quoter_a",
            password=settings.demo_password_a,
            role=Role.QUOTER,
            now=now,
        )
        _ensure_user(
            session,
            factory_id=factory_b,
            username="quoter_b",
            password=settings.demo_password_b,
            role=Role.QUOTER,
            now=now,
        )
        _ensure_user(
            session,
            factory_id=factory_a,
            username="admin_a",
            password=settings.demo_password_a,
            role=Role.ADMIN,
            now=now,
        )
        _ensure_user(
            session,
            factory_id=factory_b,
            username="admin_b",
            password=settings.demo_password_b,
            role=Role.ADMIN,
            now=now,
        )
        session.commit()
    finally:
        session.close()
