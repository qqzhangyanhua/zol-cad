from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from quote_assistant.domain.errors import InvalidFactoryPreferences
from quote_assistant.domain.risk_labels import (
    DEFAULT_RISK_LABEL_PRIORITY,
    RiskLabelName,
)

MAX_COMMON_MATERIALS = 40
MAX_MATERIAL_NAME_LENGTH = 80


@dataclass(frozen=True)
class FactoryPreferences:
    factory_id: UUID
    common_materials: tuple[str, ...]
    risk_label_priority: tuple[RiskLabelName, ...]


def default_factory_preferences(factory_id: UUID) -> FactoryPreferences:
    return FactoryPreferences(
        factory_id=factory_id,
        common_materials=(),
        risk_label_priority=DEFAULT_RISK_LABEL_PRIORITY,
    )


def normalize_common_materials(names: Sequence[str]) -> tuple[str, ...]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in names:
        name = raw.strip()
        if not name:
            raise InvalidFactoryPreferences("常用材料不能是空名称")
        if len(name) > MAX_MATERIAL_NAME_LENGTH:
            raise InvalidFactoryPreferences(f"材料名称不能超过 {MAX_MATERIAL_NAME_LENGTH} 个字")
        key = name.casefold()
        if key in seen:
            raise InvalidFactoryPreferences(f"常用材料重复：{name}")
        seen.add(key)
        cleaned.append(name)
    if len(cleaned) > MAX_COMMON_MATERIALS:
        raise InvalidFactoryPreferences(f"常用材料不能超过 {MAX_COMMON_MATERIALS} 项")
    return tuple(cleaned)


def normalize_risk_label_priority(names: Sequence[str]) -> tuple[RiskLabelName, ...]:
    parsed: list[RiskLabelName] = []
    seen: set[RiskLabelName] = set()
    for raw in names:
        try:
            label = RiskLabelName(raw)
        except ValueError as exc:
            raise InvalidFactoryPreferences(f"未知的风险标签：{raw}") from exc
        if label in seen:
            raise InvalidFactoryPreferences(f"风险标签优先级重复：{label}")
        seen.add(label)
        parsed.append(label)
    missing = [name.value for name in RiskLabelName if name not in seen]
    if missing:
        raise InvalidFactoryPreferences("风险标签优先级必须包含全部标签：" + "、".join(missing))
    return tuple(parsed)
