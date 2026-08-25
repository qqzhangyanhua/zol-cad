from __future__ import annotations

from quote_assistant.domain.confidentiality import ConfidentialityNotice
from quote_assistant.domain.entities import Actor
from quote_assistant.usecase.ports import ConfidentialityPolicySource
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_admin


class GetConfidentialityNotice(TenantBoundUseCase):
    """管理员查看保密说明。内容由 ADR-0009 与当前运行配置提供，用例不做承诺改写。"""

    def __init__(self, actor: Actor, source: ConfidentialityPolicySource) -> None:
        super().__init__(actor)
        self._source = source

    def execute(self) -> ConfidentialityNotice:
        require_admin(self.actor, "只有管理员可以查看保密说明")
        return self._source.load()
