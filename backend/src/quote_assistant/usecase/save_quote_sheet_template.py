from __future__ import annotations

from collections.abc import Sequence

from quote_assistant.domain.entities import Actor
from quote_assistant.domain.errors import InvalidQuoteSheetTemplate
from quote_assistant.domain.quote_sheet import (
    QuoteSheetTemplate,
    parse_quote_sheet_columns,
    resolve_quote_sheet_template,
)
from quote_assistant.usecase.ports import QuoteSheetTemplateRepository, UnitOfWork
from quote_assistant.usecase.tenant import TenantBoundUseCase


class SaveQuoteSheetTemplate(TenantBoundUseCase):
    """Onboarding write of a factory 报价底稿 template. Team tool, not HTTP."""

    def __init__(
        self,
        actor: Actor,
        templates: QuoteSheetTemplateRepository,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(actor)
        self._templates = templates
        self._uow = uow

    def execute(self, raw_columns: Sequence[object]) -> QuoteSheetTemplate:
        columns = parse_quote_sheet_columns(raw_columns)
        if not columns:
            raise InvalidQuoteSheetTemplate("报价底稿模板至少需要一列")
        template = QuoteSheetTemplate(columns=columns)
        self._templates.save_for_tenant(self.tenant, template)
        self._uow.commit()
        return resolve_quote_sheet_template(template)


class GetQuoteSheetTemplate(TenantBoundUseCase):
    """Onboarding read of a factory 报价底稿 template. Team tool, not HTTP."""

    def __init__(self, actor: Actor, templates: QuoteSheetTemplateRepository) -> None:
        super().__init__(actor)
        self._templates = templates

    def execute(self) -> QuoteSheetTemplate | None:
        return self._templates.get_for_tenant(self.tenant)
