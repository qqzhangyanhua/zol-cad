from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    QUOTER = "quoter"
    ADMIN = "admin"


@dataclass(frozen=True)
class User:
    id: UUID
    factory_id: UUID
    factory_name: str
    username: str
    role: Role


@dataclass(frozen=True)
class Actor:
    """Authenticated caller. factory_id is bound here, never taken from a request argument."""

    user_id: UUID
    factory_id: UUID
    factory_name: str
    username: str
    role: Role

    @classmethod
    def from_user(cls, user: User) -> Actor:
        return cls(
            user_id=user.id,
            factory_id=user.factory_id,
            factory_name=user.factory_name,
            username=user.username,
            role=user.role,
        )


@dataclass(frozen=True)
class IssuedSession:
    token: str
    user_id: UUID
    expires_at: datetime


@dataclass(frozen=True)
class PartDrawing:
    id: UUID
    factory_id: UUID
    original_filename: str
    uploaded_at: datetime
    storage_key: str
    content_type: str
    byte_size: int
    page_count: int
    selected_page: int
    uploaded_by_user_id: UUID | None


@dataclass(frozen=True)
class IncomingDrawing:
    """A file the 报价员 submitted for upload. No factory id — tenant comes from Actor."""

    original_filename: str
    content: bytes
    selected_page: int = 1


@dataclass(frozen=True)
class RejectedUpload:
    original_filename: str
    detail: str


@dataclass(frozen=True)
class UploadPartDrawingsResult:
    items: list[PartDrawing]
    rejected: list[RejectedUpload]


@dataclass(frozen=True)
class OriginalAccess:
    drawing: PartDrawing
    url: str
    expires_at: datetime
