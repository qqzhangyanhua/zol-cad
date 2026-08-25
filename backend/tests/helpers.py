from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from quote_assistant.adapter.db.models import FactoryRow, PartDrawingRow, UserRow
from quote_assistant.adapter.security.passwords import hash_password
from quote_assistant.domain.entities import Role


def create_factory(session: Session, name: str) -> UUID:
    row = FactoryRow(id=uuid4(), name=name, created_at=datetime.now(UTC))
    session.add(row)
    session.flush()
    return row.id


def create_quoter(session: Session, factory_id: UUID, username: str, password: str) -> UUID:
    row = UserRow(
        id=uuid4(),
        factory_id=factory_id,
        username=username,
        password_hash=hash_password(password),
        role=Role.QUOTER.value,
        created_at=datetime.now(UTC),
    )
    session.add(row)
    session.flush()
    return row.id


def insert_part_drawing(session: Session, factory_id: UUID, filename: str) -> UUID:
    row = PartDrawingRow(
        id=uuid4(),
        factory_id=factory_id,
        original_filename=filename,
        uploaded_at=datetime.now(UTC),
    )
    session.add(row)
    session.flush()
    return row.id


def login(client, username: str, password: str):
    return client.post("/auth/login", json={"username": username, "password": password})
