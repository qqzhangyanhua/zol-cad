from __future__ import annotations

from quote_assistant.domain.risk_labels import RiskRuleDefinition, list_risk_rule_definitions
from quote_assistant.usecase.tenant import TenantBoundUseCase, require_admin


class ListRiskRules(TenantBoundUseCase):
    """管理员只读查看当前生效的风险规则清单及阈值。"""

    def execute(self) -> tuple[RiskRuleDefinition, ...]:
        require_admin(self.actor, "只有管理员可以查看当前风险规则清单")
        return list_risk_rule_definitions()
