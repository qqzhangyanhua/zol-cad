from __future__ import annotations

from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from quote_assistant.adapter.db.models import PartDrawingRow, SessionRow, UserRow
from quote_assistant.adapter.security.passwords import verify_password
from quote_assistant.domain.entities import IssuedSession, PartDrawing, Role, User
from quote_assistant.usecase.tenant import TenantScope


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
        return [
            PartDrawing(
                id=row.id,
                factory_id=row.factory_id,
                original_filename=row.original_filename,
                uploaded_at=row.uploaded_at,
            )
            for row in rows
        ]
