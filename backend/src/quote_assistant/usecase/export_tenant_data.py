from __future__ import annotations

from datetime import UTC, datetime

from quote_assistant.domain.entities import Actor
from quote_assistant.domain.tenant_data import (
    ExportedOriginal,
    TenantArchive,
    build_tenant_archive,
)
from quote_assistant.usecase.ports import (
    CorrectionRecordRepository,
    ObjectStorage,
    PartDrawingRepository,
    QuoteTaskRepository,
    TenantArchiveWriter,
)
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_admin


class ExportTenantData(TenantBoundUseCase):
    """Export this factory's operational data as a readable zip. Tenant comes from Actor."""

    def __init__(
        self,
        actor: Actor,
        drawings: PartDrawingRepository,
        quote_tasks: QuoteTaskRepository,
        corrections: CorrectionRecordRepository,
        storage: ObjectStorage,
        writer: TenantArchiveWriter,
    ) -> None:
        super().__init__(actor)
        self._drawings = drawings
        self._quote_tasks = quote_tasks
        self._corrections = corrections
        self._storage = storage
        self._writer = writer

    def execute(self) -> tuple[TenantArchive, bytes]:
        require_admin(self.actor, "只有管理员可以导出本厂数据")
        drawings = self._drawings.list_for_tenant(self.tenant)
        originals: list[ExportedOriginal] = []
        for drawing in drawings:
            try:
                content = self._storage.fetch(drawing.storage_key)
                originals.append(
                    ExportedOriginal(
                        drawing_id=drawing.id,
                        original_filename=drawing.original_filename,
                        content=content,
                    )
                )
            except FileNotFoundError:
                originals.append(
                    ExportedOriginal(
                        drawing_id=drawing.id,
                        original_filename=drawing.original_filename,
                        content=b"",
                        missing=True,
                    )
                )
        archive = build_tenant_archive(
            factory_name=self.actor.factory_name,
            exported_at=datetime.now(UTC),
            drawings=drawings,
            quote_tasks=self._quote_tasks.list_for_tenant(self.tenant),
            corrections=self._corrections.list_for_tenant(self.tenant),
            originals=originals,
        )
        return archive, self._writer.write(archive.files)
