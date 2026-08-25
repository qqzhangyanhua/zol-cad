from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from quote_assistant.adapter.db.models import FactoryRow, UserRow
from quote_assistant.adapter.security.passwords import hash_password
from quote_assistant.config import Settings
from quote_assistant.domain.entities import Role


def seed_demo_data(session_factory: sessionmaker[Session], settings: Settings) -> None:
    session = session_factory()
    try:
        existing = session.execute(select(UserRow).limit(1)).scalar_one_or_none()
        if existing is not None:
            return
        now = datetime.now(UTC)
        factory_a = FactoryRow(id=uuid4(), name="华东精密", created_at=now)
        factory_b = FactoryRow(id=uuid4(), name="南方模具", created_at=now)
        session.add_all(
            [
                factory_a,
                factory_b,
                UserRow(
                    id=uuid4(),
                    factory_id=factory_a.id,
                    username="quoter_a",
                    password_hash=hash_password(settings.demo_password_a),
                    role=Role.QUOTER.value,
                    created_at=now,
                ),
                UserRow(
                    id=uuid4(),
                    factory_id=factory_b.id,
                    username="quoter_b",
                    password_hash=hash_password(settings.demo_password_b),
                    role=Role.QUOTER.value,
                    created_at=now,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()
