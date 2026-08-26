from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from quote_assistant.domain.entities import PartDrawing
from quote_assistant.domain.extraction import (
    CANONICAL_FIELD_BY_KEY,
    reviewable_fields,
    role_key_for_field,
)

# Honest purpose (ADR-0003): accumulate samples and iterate prompts / post-processing.
# Not live model improvement — the 提取引擎 is a closed-source general LLM.
CORRECTION_STATS_PURPOSE = (
    "这些修正记录用来积累样本，以便将来自建或微调，并迭代提示词与后处理规则。提取引擎是通用闭源大模型，修正不会回流再训练它。"
)


@dataclass(frozen=True)
class CorrectionRecord:
    """Immutable 修正记录: one edit of an extracted value. Never overwritten."""

    id: UUID
    factory_id: UUID
    part_drawing_id: UUID
    field_key: str
    field_type: str
    old_value: str | None
    new_value: str | None
    actor_user_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class CorrectionFieldTypeStat:
    """Factory-wide frequency of 修正记录, grouped by 字段类型."""

    field_type: str
    correction_count: int


def field_type_for_key(field_key: str) -> str:
    """Canonical 字段类型 for aggregation. 补录 extras roll up to the same type."""
    role = role_key_for_field(field_key)
    spec = CANONICAL_FIELD_BY_KEY.get(role)
    return spec.label if spec is not None else role


def new_correction_record(
    *,
    factory_id: UUID,
    part_drawing_id: UUID,
    field_key: str,
    old_value: str | None,
    new_value: str | None,
    actor_user_id: UUID,
    occurred_at: datetime,
) -> CorrectionRecord:
    return CorrectionRecord(
        id=uuid4(),
        factory_id=factory_id,
        part_drawing_id=part_drawing_id,
        field_key=field_key,
        field_type=field_type_for_key(field_key),
        old_value=old_value,
        new_value=new_value,
        actor_user_id=actor_user_id,
        occurred_at=occurred_at,
    )


def records_for_value_changes(
    before: PartDrawing,
    after: PartDrawing,
    *,
    actor_user_id: UUID,
    occurred_at: datetime,
) -> tuple[CorrectionRecord, ...]:
    """One 修正记录 per field whose value changed, including newly 补录 slots."""
    before_values = {field.key: field.value for field in reviewable_fields(before.extracted_fields)}
    records: list[CorrectionRecord] = []
    for field in reviewable_fields(after.extracted_fields):
        old_value = before_values.get(field.key)
        if old_value == field.value:
            continue
        records.append(
            new_correction_record(
                factory_id=after.factory_id,
                part_drawing_id=after.id,
                field_key=field.key,
                old_value=old_value,
                new_value=field.value,
                actor_user_id=actor_user_id,
                occurred_at=occurred_at,
            )
        )
    return tuple(records)


def aggregate_correction_stats(
    records: tuple[CorrectionRecord, ...] | list[CorrectionRecord],
) -> tuple[CorrectionFieldTypeStat, ...]:
    counts = Counter(record.field_type for record in records)
    return tuple(
        CorrectionFieldTypeStat(field_type=field_type, correction_count=count)
        for field_type, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )
