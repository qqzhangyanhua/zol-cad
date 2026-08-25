from __future__ import annotations

from datetime import timedelta
from typing import Protocol
from uuid import UUID

from quote_assistant.domain.correction import CorrectionRecord
from quote_assistant.domain.entities import IssuedSession, PartDrawing, User
from quote_assistant.domain.extraction import ExtractionRequest, ExtractionResult
from quote_assistant.domain.part_drawing_state import PartDrawingEvent
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

    def get_for_tenant(self, tenant: TenantScope, drawing_id: UUID) -> PartDrawing | None:
        """Load one 零件图 if it belongs to the Actor's factory."""

    def add(self, drawing: PartDrawing) -> None:
        """Persist a newly uploaded 零件图. factory_id must already be the tenant's."""

    def save(self, drawing: PartDrawing) -> None:
        """Update an existing 零件图 that already belongs to the tenant."""


class ObjectStorage(Protocol):
    """Narrow object-storage port. Use-case code must not import an OSS SDK."""

    def store(self, key: str, content: bytes, content_type: str) -> None:
        """Write bytes under key. Overwrites if the key already exists."""

    def fetch(self, key: str) -> bytes:
        """Read bytes for key. Missing keys raise FileNotFoundError."""

    def sign_access_url(self, key: str, ttl: timedelta) -> str:
        """Issue a short-lived URL that can fetch the object without public-read ACL."""

    def delete(self, key: str) -> None:
        """Remove the object. Missing keys are ignored."""


class PdfPageCounter(Protocol):
    def count_pages(self, content: bytes) -> int:
        """Return the page count of a PDF. Unreadable files raise PdfUnreadable."""


class PartDrawingEventRepository(Protocol):
    def add(self, event: PartDrawingEvent) -> None:
        """Append one timestamped state-machine event."""

    def list_for_drawing(self, tenant: TenantScope, drawing_id: UUID) -> list[PartDrawingEvent]:
        """Events of one 零件图, oldest first. Tenant-filtered."""

    def next_sequence(self, drawing_id: UUID) -> int:
        """Next sequence_no for this 零件图 (1 if none yet)."""


class CorrectionRecordRepository(Protocol):
    def add(self, record: CorrectionRecord) -> None:
        """Append one immutable 修正记录. Callers must not update existing rows."""

    def list_for_drawing(self, tenant: TenantScope, drawing_id: UUID) -> list[CorrectionRecord]:
        """修正记录 of one 零件图, oldest first. Tenant-filtered."""

    def list_for_tenant(self, tenant: TenantScope) -> list[CorrectionRecord]:
        """All 修正记录 of the Actor's factory, oldest first."""


class ExtractionEngine(Protocol):
    """Port for 读图取数. Use-case code must not import a concrete vendor SDK."""

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        """Return structured extraction plus the 图纸质量分级 signal."""


class UnitOfWork(Protocol):
    def commit(self) -> None:
        """Persist the current transaction."""
