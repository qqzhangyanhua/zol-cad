from __future__ import annotations

from uuid import UUID

from quote_assistant.domain.entities import Actor
from quote_assistant.domain.errors import IncompleteQuoteTaskReview
from quote_assistant.domain.quote_sheet import (
    QuoteSheetFile,
    QuoteSheetFileFormat,
    build_quote_sheet_table,
    incomplete_export_message,
    quote_sheet_filename,
    quote_sheet_media_type,
    resolve_quote_sheet_template,
    unreviewed_drawings_for_export,
)
from quote_assistant.usecase.ports import (
    PartDrawingRepository,
    QuoteSheetFileWriter,
    QuoteSheetTemplateRepository,
    QuoteTaskRepository,
)
from quote_assistant.usecase.tenant import (
    TenantBoundUseCase,
    filter_owned_by_actor,
    require_visible_quote_task,
)


class ExportQuoteSheet(TenantBoundUseCase):
    """Export one 报价任务 as a 报价底稿. Tenant comes from Actor, never a request arg."""

    def __init__(
        self,
        actor: Actor,
        quote_tasks: QuoteTaskRepository,
        drawings: PartDrawingRepository,
        templates: QuoteSheetTemplateRepository,
        writer: QuoteSheetFileWriter,
    ) -> None:
        super().__init__(actor)
        self._quote_tasks = quote_tasks
        self._drawings = drawings
        self._templates = templates
        self._writer = writer

    def execute(
        self, quote_task_id: UUID, file_format: QuoteSheetFileFormat
    ) -> QuoteSheetFile:
        task = require_visible_quote_task(
            self.actor, self._quote_tasks.get_for_tenant(self.tenant, quote_task_id)
        )
        all_drawings = self._drawings.list_for_quote_task(self.tenant, quote_task_id)
        unfinished = unreviewed_drawings_for_export(all_drawings)
        if unfinished:
            visible_unfinished = filter_owned_by_actor(
                self.actor,
                unfinished,
                lambda drawing: drawing.uploaded_by_user_id,
            )
            raise IncompleteQuoteTaskReview(
                incomplete_export_message(unfinished, visible_unfinished=visible_unfinished)
            )
        drawings = filter_owned_by_actor(
            self.actor,
            all_drawings,
            lambda drawing: drawing.uploaded_by_user_id,
        )
        template = resolve_quote_sheet_template(self._templates.get_for_tenant(self.tenant))
        table = build_quote_sheet_table(drawings, template)
        content = self._writer.write(table.headers, table.rows, file_format)
        return QuoteSheetFile(
            filename=quote_sheet_filename(task.name, file_format),
            media_type=quote_sheet_media_type(file_format),
            content=content,
        )
