from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from quote_assistant.domain.entities import Role


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class OkResponse(BaseModel):
    ok: bool = True


class CurrentUserResponse(BaseModel):
    username: str
    factory_name: str
    role: Role


class PartDrawingResponse(BaseModel):
    id: UUID
    original_filename: str
    uploaded_at: datetime


class PartDrawingListResponse(BaseModel):
    items: list[PartDrawingResponse]
