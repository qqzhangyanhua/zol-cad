import { isRecord } from "@/lib/types/guard";

export const RISK_LABEL_NAMES = ["高精度", "深孔", "薄壁", "细长"] as const;
export type RiskLabelName = (typeof RISK_LABEL_NAMES)[number];

export type RiskLabel = {
  name: RiskLabelName;
  rule_id: string;
  triggering_value: string;
  reason: string;
};

export type RiskRule = {
  rule_id: string;
  label_name: RiskLabelName;
  threshold: string;
  description: string;
  provisional: boolean;
};

export type RiskRuleList = {
  items: RiskRule[];
};

export function isRiskLabelName(value: unknown): value is RiskLabelName {
  return (RISK_LABEL_NAMES as readonly string[]).includes(value as string);
}

export function parseRiskLabel(data: unknown): RiskLabel {
  if (!isRecord(data)) {
    throw new Error("风险标签响应格式不正确");
  }
  if (
    !isRiskLabelName(data.name) ||
    typeof data.rule_id !== "string" ||
    typeof data.triggering_value !== "string" ||
    typeof data.reason !== "string"
  ) {
    throw new Error("风险标签响应格式不正确");
  }
  return {
    name: data.name,
    rule_id: data.rule_id,
    triggering_value: data.triggering_value,
    reason: data.reason,
  };
}

export function parseRiskRuleList(data: unknown): RiskRuleList {
  if (!isRecord(data) || !Array.isArray(data.items)) {
    throw new Error("风险规则响应格式不正确");
  }
  return {
    items: data.items.map((item) => {
      if (
        !isRecord(item) ||
        typeof item.rule_id !== "string" ||
        !isRiskLabelName(item.label_name) ||
        typeof item.threshold !== "string" ||
        typeof item.description !== "string" ||
        typeof item.provisional !== "boolean"
      ) {
        throw new Error("风险规则响应格式不正确");
      }
      return {
        rule_id: item.rule_id,
        label_name: item.label_name,
        threshold: item.threshold,
        description: item.description,
        provisional: item.provisional,
      };
    }),
  };
}

export function sortRiskLabels(labels: RiskLabel[], priority: readonly RiskLabelName[]): RiskLabel[] {
  const rank = new Map(priority.map((name, index) => [name, index]));
  return [...labels].sort((left, right) => {
    const leftRank = rank.get(left.name) ?? priority.length;
    const rightRank = rank.get(right.name) ?? priority.length;
    return leftRank - rightRank;
  });
}
