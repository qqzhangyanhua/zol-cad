from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class FactoryRow(Base):
    __tablename__ = "factories"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    users: Mapped[list[UserRow]] = relationship(back_populates="factory")


class UserRow(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("username", name="uq_users_username"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    factory_id: Mapped[UUID] = mapped_column(ForeignKey("factories.id"), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    factory: Mapped[FactoryRow] = relationship(back_populates="users")


class PartDrawingRow(Base):
    __tablename__ = "part_drawings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    factory_id: Mapped[UUID] = mapped_column(ForeignKey("factories.id"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(800), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    byte_size: Mapped[int] = mapped_column(nullable=False)
    page_count: Mapped[int] = mapped_column(nullable=False)
    selected_page: Mapped[int] = mapped_column(nullable=False)
    uploaded_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    quality_grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_assembly_or_exploded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    low_quality_unreliable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    extracted_fields: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    stashed_extracted_fields: Mapped[list[dict[str, object]] | None] = mapped_column(
        JSONB, nullable=True
    )
    extraction_failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    part_family_id: Mapped[str] = mapped_column(String(80), nullable=False)
    quote_task_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("quote_tasks.id"), nullable=True, index=True
    )


class PartDrawingEventRow(Base):
    __tablename__ = "part_drawing_events"
    __table_args__ = (
        UniqueConstraint("part_drawing_id", "sequence_no", name="uq_part_drawing_events_sequence"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    part_drawing_id: Mapped[UUID] = mapped_column(
        ForeignKey("part_drawings.id"), nullable=False, index=True
    )
    factory_id: Mapped[UUID] = mapped_column(ForeignKey("factories.id"), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class CorrectionRecordRow(Base):
    """Append-only 修正记录. Rows are never updated or overwritten."""

    __tablename__ = "correction_records"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    factory_id: Mapped[UUID] = mapped_column(ForeignKey("factories.id"), nullable=False, index=True)
    part_drawing_id: Mapped[UUID] = mapped_column(
        ForeignKey("part_drawings.id"), nullable=False, index=True
    )
    field_key: Mapped[str] = mapped_column(String(80), nullable=False)
    field_type: Mapped[str] = mapped_column(String(40), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class QuoteTaskRow(Base):
    __tablename__ = "quote_tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    factory_id: Mapped[UUID] = mapped_column(ForeignKey("factories.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)


class FactoryPreferenceRow(Base):
    """Per-factory 常用材料 and 风险标签 display priority. No 报价底稿 mapping here."""

    __tablename__ = "factory_preferences"

    factory_id: Mapped[UUID] = mapped_column(ForeignKey("factories.id"), primary_key=True)
    common_materials: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    risk_label_priority: Mapped[list[str]] = mapped_column(JSONB, nullable=False)


class QuoteSheetTemplateRow(Base):
    """Backend-maintained 报价底稿 column template. One row per factory; no admin UI."""

    __tablename__ = "quote_sheet_templates"

    factory_id: Mapped[UUID] = mapped_column(ForeignKey("factories.id"), primary_key=True)
    columns: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)


class ManualBaselineRow(Base):
    __tablename__ = "manual_baselines"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    factory_id: Mapped[UUID] = mapped_column(ForeignKey("factories.id"), nullable=False, index=True)
    part_description: Mapped[str] = mapped_column(String(200), nullable=False)
    manual_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)


class TenantDeleteChallengeRow(Base):
    """One-time admin confirmation for deleting this factory's operational data."""

    __tablename__ = "tenant_delete_challenges"
    __table_args__ = (UniqueConstraint("token", name="uq_tenant_delete_challenges_token"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    factory_id: Mapped[UUID] = mapped_column(ForeignKey("factories.id"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(128), nullable=False)
    required_phrase: Mapped[str] = mapped_column(String(200), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SessionRow(Base):
    __tablename__ = "sessions"
    __table_args__ = (UniqueConstraint("token", name="uq_sessions_token"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    token: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
