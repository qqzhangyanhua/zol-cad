from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
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


class SessionRow(Base):
    __tablename__ = "sessions"
    __table_args__ = (UniqueConstraint("token", name="uq_sessions_token"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    token: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
