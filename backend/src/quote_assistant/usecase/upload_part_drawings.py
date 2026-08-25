from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from quote_assistant.domain.drawing_upload import (
    MAX_FILE_BYTES,
    PDF_MEDIA_TYPE,
    assess_drawing_upload,
    detect_media_type,
)
from quote_assistant.domain.entities import (
    Actor,
    IncomingDrawing,
    PartDrawing,
    PartDrawingStatus,
    RejectedUpload,
    UploadPartDrawingsResult,
)
from quote_assistant.domain.errors import PdfUnreadable
from quote_assistant.domain.extraction import ExtractionRequest
from quote_assistant.domain.part_drawing_state import (
    birth_uploaded,
    record_transition,
    status_after_grade,
)
from quote_assistant.usecase.extract_part_drawing import apply_extraction
from quote_assistant.usecase.ports import (
    ExtractionEngine,
    ObjectStorage,
    PartDrawingEventRepository,
    PartDrawingRepository,
    PdfPageCounter,
    UnitOfWork,
)
from quote_assistant.usecase.tenant import TenantBoundUseCase


def _storage_suffix(media_type: str, original_filename: str) -> str:
    suffix = Path(original_filename).suffix.lower()
    allowed = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".tif",
        ".tiff",
    }
    if suffix in allowed:
        return suffix
    return {
        "application/pdf": ".pdf",
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/tiff": ".tiff",
    }.get(media_type, "")


class UploadPartDrawings(TenantBoundUseCase):
    """Store one or more 零件图 for the authenticated 报价员's factory, then grade them."""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        events: PartDrawingEventRepository,
        storage: ObjectStorage,
        pdf_pages: PdfPageCounter,
        engine: ExtractionEngine,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._events = events
        self._storage = storage
        self._pdf_pages = pdf_pages
        self._engine = engine
        self._uow = uow

    def execute(self, files: list[IncomingDrawing]) -> UploadPartDrawingsResult:
        accepted: list[PartDrawing] = []
        rejected: list[RejectedUpload] = []
        stored_keys: list[str] = []
        try:
            for incoming in files:
                page_count: int | None = None
                if (
                    detect_media_type(incoming.content) == PDF_MEDIA_TYPE
                    and len(incoming.content) <= MAX_FILE_BYTES
                ):
                    try:
                        page_count = self._pdf_pages.count_pages(incoming.content)
                    except PdfUnreadable:
                        rejected.append(
                            RejectedUpload(
                                original_filename=incoming.original_filename or "未命名文件",
                                detail=(
                                    f"文件「{incoming.original_filename or '未命名文件'}」无法读取 PDF 页数"
                                ),
                            )
                        )
                        continue
                assessed = assess_drawing_upload(
                    original_filename=incoming.original_filename,
                    content=incoming.content,
                    selected_page=incoming.selected_page,
                    pdf_page_count=page_count,
                )
                if isinstance(assessed, str):
                    rejected.append(
                        RejectedUpload(
                            original_filename=incoming.original_filename or "未命名文件",
                            detail=assessed,
                        )
                    )
                    continue
                drawing_id = uuid4()
                suffix = _storage_suffix(assessed.media_type, assessed.original_filename)
                storage_key = (
                    f"part-drawings/{self.tenant.factory_id}/{drawing_id}/original{suffix}"
                )
                self._storage.store(storage_key, assessed.content, assessed.media_type)
                stored_keys.append(storage_key)
                now = datetime.now(UTC)
                drawing = PartDrawing(
                    id=drawing_id,
                    factory_id=self.tenant.factory_id,
                    original_filename=assessed.original_filename,
                    uploaded_at=now,
                    storage_key=storage_key,
                    content_type=assessed.media_type,
                    byte_size=assessed.byte_size,
                    page_count=assessed.page_count,
                    selected_page=assessed.selected_page,
                    uploaded_by_user_id=self.actor.user_id,
                    status=PartDrawingStatus.UPLOADED,
                    quality_grade=None,
                    is_assembly_or_exploded=False,
                    low_quality_unreliable=False,
                    extracted_fields=(),
                    extraction_failure_reason=None,
                )
                drawing, born = birth_uploaded(
                    drawing, occurred_at=now, actor_user_id=self.actor.user_id
                )
                self._drawings.add(drawing)
                self._events.add(born)
                drawing, grading = record_transition(
                    drawing,
                    PartDrawingStatus.GRADING,
                    occurred_at=datetime.now(UTC),
                    sequence_no=2,
                    actor_user_id=self.actor.user_id,
                )
                self._drawings.save(drawing)
                self._events.add(grading)

                page_content = self._storage.fetch(storage_key)
                result = self._engine.extract(
                    ExtractionRequest(
                        page_content=page_content,
                        media_type=assessed.media_type,
                        part_family_id=None,
                        input_drawing_id=assessed.original_filename,
                    )
                )
                next_status = status_after_grade(result)
                drawing, graded = record_transition(
                    drawing,
                    next_status,
                    occurred_at=datetime.now(UTC),
                    sequence_no=3,
                    actor_user_id=self.actor.user_id,
                    quality_grade=result.quality_grade,
                    is_assembly_or_exploded=result.is_assembly_or_exploded,
                )
                self._drawings.save(drawing)
                self._events.add(graded)
                if next_status is PartDrawingStatus.GRADED:
                    drawing = apply_extraction(
                        drawing,
                        actor_user_id=self.actor.user_id,
                        drawings=self._drawings,
                        events=self._events,
                        storage=self._storage,
                        engine=self._engine,
                    )
                accepted.append(drawing)
            self._uow.commit()
        except Exception:
            for key in stored_keys:
                self._storage.delete(key)
            raise
        return UploadPartDrawingsResult(items=accepted, rejected=rejected)
