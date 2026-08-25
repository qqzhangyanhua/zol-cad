from __future__ import annotations

from dataclasses import dataclass

from quote_assistant.domain.part_family import (
    PROVISIONAL_OTHER_PART_FAMILY_ID,
    TARGET_PART_FAMILY_ID,
    UNKNOWN_PART_FAMILY_ID,
)


@dataclass(frozen=True)
class PromptTemplate:
    """One 读图取数 prompt, keyed by 零件族. Bodies are placeholders until ticket 01."""

    id: str
    family_id: str
    body: str


# Dedicated template for the provisional target. Body is a structural placeholder —
# not a researched turning/milling prompt. Ticket 01 will replace the text.
_TARGET_FAMILY_PROMPT = PromptTemplate(
    id="prompt.provisional-target-family",
    family_id=TARGET_PART_FAMILY_ID,
    body=(
        "【专用模板·暂定】票 01 尚未用真实样本选定目标零件族。"
        "本模板仅占位，供机制把目标族专用提示与通用提示分开。"
        "选定后替换正文。请提取标题栏、关键尺寸与技术要求；图上没有的字段留空。"
    ),
)

_GENERIC_EXPERIMENTAL_PROMPT = PromptTemplate(
    id="prompt.generic-experimental",
    family_id=UNKNOWN_PART_FAMILY_ID,
    body=(
        "【通用模板·实验性】本图不属于当前暂定目标零件族（或族类未知）。"
        "请提取标题栏、关键尺寸与技术要求；图上没有的字段留空。"
        "结果须按产品规则标注实验性、不保证。"
    ),
)

# Central catalog. Call sites pass 族类 only; they must not inline prompt text.
_TEMPLATES_BY_FAMILY: dict[str, PromptTemplate] = {
    TARGET_PART_FAMILY_ID: _TARGET_FAMILY_PROMPT,
    PROVISIONAL_OTHER_PART_FAMILY_ID: _GENERIC_EXPERIMENTAL_PROMPT,
    UNKNOWN_PART_FAMILY_ID: _GENERIC_EXPERIMENTAL_PROMPT,
}


def prompt_template_for(family_id: str) -> PromptTemplate:
    """Resolve the centralized template for a 零件族. Unknown families get the generic one."""
    return _TEMPLATES_BY_FAMILY.get(family_id, _GENERIC_EXPERIMENTAL_PROMPT)
