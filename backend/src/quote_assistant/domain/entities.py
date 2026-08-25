from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from quote_assistant.domain.extraction import ExtractedField
from quote_assistant.domain.quality import QualityGrade


class PartDrawingStatus(StrEnum):
    UPLOADED = "已上传"
    GRADING = "分级中"
    GRADED = "已分级"
    ADVISE_MANUAL = "建议人工"
    OUT_OF_SCOPE = "不在范围"
    EXTRACTING = "提取中"
    EXTRACTED = "已提取"
    EXTRACT_FAILED = "提取失败"
    REVIEWING = "复核中"
    REVIEWED = "已复核"


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
    created_at: datetime
    disabled_at: datetime | None


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
    status: PartDrawingStatus
    quality_grade: QualityGrade | None
    is_assembly_or_exploded: bool
    low_quality_unreliable: bool
    extracted_fields: tuple[ExtractedField, ...]
    extraction_failure_reason: str | None
    part_family_id: str
    quote_task_id: UUID | None


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


@dataclass(frozen=True)
class ManualBaseline:
    """一条管理员录入的纯人工作业计时，作为处理耗时的对照。"""

    id: UUID
    factory_id: UUID
    part_description: str
    manual_duration_seconds: int
    recorded_at: datetime
    recorded_by_user_id: UUID


@dataclass(frozen=True)
class DrawingProcessingTime:
    """一张已复核零件图由事件时间戳算出的处理耗时。"""

    part_drawing_id: UUID
    original_filename: str
    uploaded_at: datetime
    reviewed_at: datetime
    processing_seconds: float
    grading_seconds: float | None
    extraction_seconds: float | None
    review_seconds: float | None


@dataclass(frozen=True)
class FactoryProcessingRecord:
    """管理员看到的一条全厂处理记录：谁上传了哪张零件图、当前状态。"""

    part_drawing_id: UUID
    original_filename: str
    uploaded_at: datetime
    status: PartDrawingStatus
    uploaded_by_user_id: UUID | None
    uploaded_by_username: str | None
    quote_task_id: UUID | None
    quality_grade: QualityGrade | None


@dataclass(frozen=True)
class ProcessingTimeComparison:
    """本厂处理耗时与人工基线的对照。未复核零件图不计入。"""

    reviewed_count: int
    excluded_unreviewed_count: int
    average_processing_seconds: float | None
    average_grading_seconds: float | None
    average_extraction_seconds: float | None
    average_review_seconds: float | None
    baseline_count: int
    average_baseline_seconds: float | None
    saved_seconds: float | None
    items: tuple[DrawingProcessingTime, ...]
    baselines: tuple[ManualBaseline, ...]
