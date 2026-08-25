from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum

from quote_assistant.domain.extraction import ExtractedField, role_key_for_field

# Closed output vocabulary. Type-level invariant: no 安全 / 无风险 / 通过.
# A false "无深孔风险" would make the 报价员 skip a price uplift (ADR-0007).


class RiskLabelName(StrEnum):
    HIGH_PRECISION = "高精度"
    DEEP_HOLE = "深孔"
    THIN_WALL = "薄壁"
    SLENDER = "细长"


RISK_LABEL_VOCABULARY: frozenset[RiskLabelName] = frozenset(RiskLabelName)
FORBIDDEN_RISK_LABEL_SEMANTICS: frozenset[str] = frozenset({"安全", "无风险", "通过"})

NO_JUDGABLE_RISK_ITEMS_MESSAGE = "未发现可判定的风险项，不代表此件无风险"

# --- Provisional thresholds (pending ticket 01). Not researched truth. ---
# Named examples from this ticket and ADR-0007:
PROVISIONAL_IT_GRADE_MAX = 6  # 公差 ≤ IT6 → 高精度
PROVISIONAL_DEPTH_TO_DIAMETER_GT = Decimal("5")  # 孔深/孔径 > 5 → 深孔
# Additional labels named in the ticket / ADR, thresholds invented only to wire
# the engine. Replace after ticket 01 sample research. Do not treat as shop truth.
PROVISIONAL_THIN_WALL_MM_MAX = Decimal("2")  # 最薄壁 ≤ 2 mm → 薄壁
PROVISIONAL_SLENDERNESS_GT = Decimal("10")  # 长度/直径 > 10 → 细长

_IT_GRADE = re.compile(r"(?i)\bIT\s*0*(\d+)\b")
_DIAMETER_BY_LENGTH = re.compile(
    r"(?:[ØøφΦ⌀]\s*)?(?P<diameter>\d+(?:\.\d+)?)\s*[×xX*]\s*(?P<length>\d+(?:\.\d+)?)"
)
_MILLIMETRES = re.compile(r"^(?P<value>\d+(?:\.\d+)?)\s*(?:mm|MM)?$")


@dataclass(frozen=True)
class RiskLabel:
    name: RiskLabelName
    rule_id: str
    triggering_value: str
    reason: str


def evaluate_risk_labels(fields: Sequence[ExtractedField]) -> tuple[RiskLabel, ...]:
    """Pure function: current structured data in, fired 风险标签 out.

    No IO, no randomness, no time. Missing or unparseable values do not fire;
    silence is not safety — the display layer carries that meaning.
    """
    values = _values_by_role(fields)
    fired: list[RiskLabel] = []
    for rule in _PROVISIONAL_RULES:
        label = rule(values)
        if label is not None:
            fired.append(label)
    return tuple(fired)


def _values_by_role(fields: Sequence[ExtractedField]) -> dict[str, tuple[str, ...]]:
    """Current 报价员-visible values, keyed by canonical role.

    Ignored items are excluded so 风险标签 follow confirmed / 补录 values,
    not an inapplicable AI row. Extra 补录 keys map back to their role.
    """
    buckets: dict[str, list[str]] = {}
    for field in fields:
        if field.ignored or field.value is None or field.value == "":
            continue
        role = role_key_for_field(field.key)
        buckets.setdefault(role, []).append(field.value)
    return {role: tuple(raw_values) for role, raw_values in buckets.items()}


def _role_values(values: Mapping[str, tuple[str, ...]], key: str) -> tuple[str, ...]:
    return values.get(key, ())


def _parse_it_grade(raw: str) -> int | None:
    match = _IT_GRADE.search(raw)
    if match is None:
        return None
    return int(match.group(1))


def _parse_pair(raw: str) -> tuple[Decimal, Decimal] | None:
    match = _DIAMETER_BY_LENGTH.search(raw)
    if match is None:
        return None
    try:
        diameter = Decimal(match.group("diameter"))
        length = Decimal(match.group("length"))
    except InvalidOperation:
        return None
    if diameter <= 0 or length <= 0:
        return None
    return diameter, length


def _parse_millimetres(raw: str) -> Decimal | None:
    match = _MILLIMETRES.match(raw.strip())
    if match is None:
        return None
    try:
        value = Decimal(match.group("value"))
    except InvalidOperation:
        return None
    if value < 0:
        return None
    return value


def _high_precision(values: Mapping[str, tuple[str, ...]]) -> RiskLabel | None:
    for raw in _role_values(values, "tightest_tolerance"):
        grade = _parse_it_grade(raw)
        if grade is None or grade > PROVISIONAL_IT_GRADE_MAX:
            continue
        return RiskLabel(
            name=RiskLabelName.HIGH_PRECISION,
            rule_id="RL-HIGH-PREC",
            triggering_value=raw,
            reason=(
                f"最严公差 {raw} 不粗于暂定门槛 IT{PROVISIONAL_IT_GRADE_MAX}"
                "（ADR-0007 示例，待票 01 调研确认）"
            ),
        )
    return None


def _deep_hole(values: Mapping[str, tuple[str, ...]]) -> RiskLabel | None:
    for raw in _role_values(values, "deepest_hole"):
        parsed = _parse_pair(raw)
        if parsed is None:
            continue
        diameter, depth = parsed
        ratio = depth / diameter
        if ratio <= PROVISIONAL_DEPTH_TO_DIAMETER_GT:
            continue
        return RiskLabel(
            name=RiskLabelName.DEEP_HOLE,
            rule_id="RL-DEEP-HOLE",
            triggering_value=raw,
            reason=(
                f"最深孔 {raw} 的孔深/孔径为 {ratio:.2f}，大于暂定门槛 "
                f"{PROVISIONAL_DEPTH_TO_DIAMETER_GT}"
                "（ADR-0007 示例，待票 01 调研确认）"
            ),
        )
    return None


def _thin_wall(values: Mapping[str, tuple[str, ...]]) -> RiskLabel | None:
    for raw in _role_values(values, "thinnest_wall"):
        thickness = _parse_millimetres(raw)
        if thickness is None or thickness > PROVISIONAL_THIN_WALL_MM_MAX:
            continue
        return RiskLabel(
            name=RiskLabelName.THIN_WALL,
            rule_id="RL-THIN-WALL",
            triggering_value=raw,
            reason=(
                f"最薄壁 {raw} 达到暂定门槛 {PROVISIONAL_THIN_WALL_MM_MAX} mm"
                "（接线用占位，待票 01 调研确认，非样本结论）"
            ),
        )
    return None


def _slender(values: Mapping[str, tuple[str, ...]]) -> RiskLabel | None:
    for raw in _role_values(values, "max_envelope"):
        parsed = _parse_pair(raw)
        if parsed is None:
            continue
        diameter, length = parsed
        ratio = length / diameter
        if ratio <= PROVISIONAL_SLENDERNESS_GT:
            continue
        return RiskLabel(
            name=RiskLabelName.SLENDER,
            rule_id="RL-SLENDER",
            triggering_value=raw,
            reason=(
                f"最大外形 {raw} 的长度/直径为 {ratio:.2f}，大于暂定门槛 "
                f"{PROVISIONAL_SLENDERNESS_GT}"
                "（接线用占位，待票 01 调研确认，非样本结论）"
            ),
        )
    return None


_PROVISIONAL_RULES = (_high_precision, _deep_hole, _thin_wall, _slender)
