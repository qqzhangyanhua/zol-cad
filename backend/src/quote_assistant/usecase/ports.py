from __future__ import annotations

from datetime import timedelta
from typing import Protocol
from uuid import UUID

from quote_assistant.domain.entities import IssuedSession, PartDrawing, User
from quote_assistant.usecase.tenant import TenantScope


class PasswordAuthenticator(Protocol):
    def authenticate(self, username: str, password: str) -> User | None:
        """Return the user when credentials match; otherwise None."""


class UserRepository(Protocol):
    def get_by_id(self, user_id: UUID) -> User | None:
        """Load a user by id, including factory name."""


class SessionRepository(Protocol):
    def create(self, user_id: UUID, ttl: timedelta) -> IssuedSession:
        """Issue a new opaque session token."""

    def get_valid(self, token: str) -> IssuedSession | None:
        """Return the session if it exists and has not expired."""

    def revoke(self, token: str) -> None:
        """Invalidate the session. Missing tokens are ignored."""


class PartDrawingRepository(Protocol):
    def list_for_tenant(self, tenant: TenantScope) -> list[PartDrawing]:
        """List 零件图 belonging to the Actor's factory only."""


class UnitOfWork(Protocol):
    def commit(self) -> None:
        """Persist the current transaction."""
