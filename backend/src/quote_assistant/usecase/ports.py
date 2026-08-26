from __future__ import annotations

from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from quote_assistant.domain.correction import CorrectionRecord
from quote_assistant.domain.entities import (
    Actor,
    IssuedSession,
    ManualBaseline,
    PartDrawing,
    User,
)
from quote_assistant.domain.factory_preferences import FactoryPreferences
from quote_assistant.domain.quote_sheet import QuoteSheetFileFormat, QuoteSheetTemplate
from quote_assistant.domain.quote_task import QuoteTask
from quote_assistant.domain.confidentiality import ConfidentialityNotice
from quote_assistant.domain.extraction import ExtractionRequest, ExtractionResult, RenderedPage
from quote_assistant.domain.part_drawing_state import PartDrawingEvent
from quote_assistant.domain.tenant_data import TenantArchiveFile, TenantDeleteChallenge
from quote_assistant.usecase.tenant import TenantScope


class PasswordAuthenticator(Protocol):
    def authenticate(self, username: str, password: str) -> User | None:
        """Return the user when credentials match; otherwise None."""


class PasswordHasher(Protocol):
    def hash_password(self, password: str) -> str:
        """Hash a new 报价员 password. Adapter implements this; use cases stay IO-free."""


class UserRepository(Protocol):
    def get_by_id(self, user_id: UUID) -> User | None:
        """Load a user by id, including factory name."""

    def get_by_username(self, username: str) -> User | None:
        """Load a user by username, including factory name."""

    def list_for_tenant(self, tenant: TenantScope) -> list[User]:
        """Users of the Actor's factory, newest first."""

    def add(self, user: User, password_hash: str) -> None:
        """Persist a newly created 报价员. factory_id must already be the tenant's."""

    def disable(self, tenant: TenantScope, user_id: UUID) -> User | None:
        """Set disabled_at if the user belongs to the tenant. Idempotent when already disabled."""


class SessionRepository(Protocol):
    def create(self, user_id: UUID, ttl: timedelta) -> IssuedSession:
        """Issue a new opaque session token."""

    def get_valid(self, token: str) -> IssuedSession | None:
        """Return the session if it exists and has not expired."""

    def revoke(self, token: str) -> None:
        """Invalidate the session. Missing tokens are ignored."""

    def revoke_for_user(self, user_id: UUID) -> None:
        """Invalidate every session of this user. Used when 停用账号."""


class PartDrawingRepository(Protocol):
    def list_for_tenant(self, tenant: TenantScope) -> list[PartDrawing]:
        """List 零件图 belonging to the Actor's factory only."""

    def get_for_tenant(self, tenant: TenantScope, drawing_id: UUID) -> PartDrawing | None:
        """Load one 零件图 if it belongs to the Actor's factory."""

    def list_for_quote_task(self, tenant: TenantScope, quote_task_id: UUID) -> list[PartDrawing]:
        """零件图 belonging to one 报价任务 of the Actor's factory, oldest first."""

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


class DrawingPageRenderer(Protocol):
    """Port that turns a stored 零件图 into the one page the 提取引擎 sees.

    Use-case code must not import a PDF library; both the 分级 call and the
    读图取数 call go through here so 选定页 can never be bypassed on one path.
    """

    def render(self, content: bytes, media_type: str, selected_page: int) -> RenderedPage:
        """PDF → 指定页的图像；图片原样返回。渲染不出来时抛 PageRenderFailed。"""


class InFlightPartDrawingRepository(Protocol):
    """Cross-tenant maintenance read. Only the startup recovery sweep may use this.

    Deliberately separate from PartDrawingRepository so the tenant-filtered port keeps
    having no way to read across factories.
    """

    def list_in_flight(self) -> list[PartDrawing]:
        """零件图 stuck in 分级中 / 提取中, any factory."""

    def save(self, drawing: PartDrawing) -> None:
        """Update one 零件图 without a tenant scope. Recovery only."""


class PartDrawingProcessor(Protocol):
    """Port for 分级 + 读图取数 that must not block the 报价员's upload request.

    Returning the finished 零件图 means the work ran inline; returning None means it was
    deferred and the caller should report the drawing as-is and let the client poll.
    """

    def submit(self, actor: Actor, drawing_id: UUID) -> PartDrawing | None:
        """Process now or later, on behalf of the uploading 报价员."""


class PartDrawingEventRepository(Protocol):
    def add(self, event: PartDrawingEvent) -> None:
        """Append one timestamped state-machine event."""

    def list_for_drawing(self, tenant: TenantScope, drawing_id: UUID) -> list[PartDrawingEvent]:
        """Events of one 零件图, oldest first. Tenant-filtered."""

    def next_sequence(self, drawing_id: UUID) -> int:
        """Next sequence_no for this 零件图 (1 if none yet)."""

    def list_for_tenant(self, tenant: TenantScope) -> list[PartDrawingEvent]:
        """All timestamped events of the Actor's factory, oldest first."""


class ManualBaselineRepository(Protocol):
    def add(self, baseline: ManualBaseline) -> None:
        """Persist one admin-entered 人工基线. factory_id must already be the tenant's."""

    def list_for_tenant(self, tenant: TenantScope) -> list[ManualBaseline]:
        """人工基线 belonging to the Actor's factory only, newest first."""


class CorrectionRecordRepository(Protocol):
    def add(self, record: CorrectionRecord) -> None:
        """Append one immutable 修正记录. Callers must not update existing rows."""

    def list_for_drawing(self, tenant: TenantScope, drawing_id: UUID) -> list[CorrectionRecord]:
        """修正记录 of one 零件图, oldest first. Tenant-filtered."""

    def list_for_tenant(self, tenant: TenantScope) -> list[CorrectionRecord]:
        """All 修正记录 of the Actor's factory, oldest first."""


class QuoteTaskRepository(Protocol):
    def add(self, task: QuoteTask) -> None:
        """Persist a newly created 报价任务. factory_id must already be the tenant's."""

    def get_for_tenant(self, tenant: TenantScope, task_id: UUID) -> QuoteTask | None:
        """Load one 报价任务 if it belongs to the Actor's factory."""

    def list_for_tenant(
        self,
        tenant: TenantScope,
        *,
        customer_name: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> list[QuoteTask]:
        """报价任务 of the Actor's factory, newest first. Optional customer/time filters."""


class FactoryPreferenceRepository(Protocol):
    def get_for_tenant(self, tenant: TenantScope) -> FactoryPreferences | None:
        """本厂常用材料与风险标签优先级。Missing row means defaults."""

    def save_for_tenant(self, tenant: TenantScope, preferences: FactoryPreferences) -> None:
        """Upsert this factory's preferences. Tenant comes from Actor."""


class QuoteSheetTemplateRepository(Protocol):
    """Per-factory 报价底稿 column template. Onboarding writes this; no product UI."""

    def get_for_tenant(self, tenant: TenantScope) -> QuoteSheetTemplate | None:
        """Load the Actor's factory template, or None to use the backend default."""

    def save_for_tenant(self, tenant: TenantScope, template: QuoteSheetTemplate) -> None:
        """Upsert the Actor's factory template. Used by onboarding / tests, not HTTP."""


class QuoteSheetFileWriter(Protocol):
    def write(
        self,
        headers: tuple[str, ...],
        rows: tuple[tuple[str, ...], ...],
        file_format: QuoteSheetFileFormat,
    ) -> bytes:
        """Turn a finished table into xlsx or csv bytes. No domain decisions."""


class TenantArchiveWriter(Protocol):
    def write(self, files: tuple[TenantArchiveFile, ...]) -> bytes:
        """Pack already-built export files into a zip. No domain decisions."""


class TenantDeleteChallengeRepository(Protocol):
    def add(self, challenge: TenantDeleteChallenge) -> None:
        """Persist a newly issued one-time delete confirmation. Tenant comes from the entity."""

    def get_open(self, tenant: TenantScope, token: str, now: datetime) -> TenantDeleteChallenge | None:
        """Load an unused, unexpired challenge that belongs to this factory."""

    def mark_consumed(self, tenant: TenantScope, token: str, consumed_at: datetime) -> None:
        """Mark the challenge used. Missing tokens are ignored."""


class TenantDataPurge(Protocol):
    def delete_operational_data(self, tenant: TenantScope) -> None:
        """Delete this factory's 零件图, events, 修正记录, 报价任务, 人工基线, preferences, challenges."""


class ExtractionEngine(Protocol):
    """Port for 读图取数. Use-case code must not import a concrete vendor SDK.

    extract() returns a validated ExtractionResult, or raises:
    - ExtractionValidationFailed: adapter-boundary schema rejected the payload
    - ExtractionEngineFailed: transport / timeout / rate-limit / vendor-unselected
    """

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        """Return structured extraction plus the 图纸质量分级 signal."""


class ConfidentialityPolicySource(Protocol):
    """Read-only source for the admin 保密说明. Adapter parses ADR-0009; use-case stays IO-free."""

    def load(self) -> ConfidentialityNotice:
        """Current honesty-first notice. Must not invent DPA / training / region promises."""


class UnitOfWork(Protocol):
    def commit(self) -> None:
        """Persist the current transaction."""
