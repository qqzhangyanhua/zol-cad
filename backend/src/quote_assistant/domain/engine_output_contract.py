from __future__ import annotations

import json

from quote_assistant.domain.extraction import CANONICAL_FIELD_BY_KEY
from quote_assistant.domain.quality import QualityGrade

# Prompt contract: absent field values are JSON null.
# The adapter also accepts "" and normalizes it to None
# (EngineFieldPayload.blank_value_is_missing); the prompt does not ask for "".
ENGINE_ABSENT_FIELD_VALUE: None = None

ENGINE_RESULT_REQUIRED_KEYS: tuple[str, ...] = (
    "quality_grade",
    "is_assembly_or_exploded",
    "fields",
)

ENGINE_FIELD_REQUIRED_KEYS: tuple[str, ...] = ("key", "label", "value", "category")


def quality_grade_values() -> tuple[str, ...]:
    return tuple(grade.value for grade in QualityGrade)


def field_catalog_lines() -> tuple[str, ...]:
    """One prompt line per catalog field. Generated from CANONICAL_FIELD_BY_KEY."""
    return tuple(
        f"- key={spec.key} | label={spec.label} | category={spec.category.value}"
        for spec in CANONICAL_FIELD_BY_KEY.values()
    )


def engine_output_contract_example() -> dict[str, object]:
    """A payload that follows the prompt contract. Used in the prompt and in tests."""
    return {
        "quality_grade": QualityGrade.CLEAR.value,
        "is_assembly_or_exploded": False,
        "fields": [
            {
                "key": spec.key,
                "label": spec.label,
                "value": ENGINE_ABSENT_FIELD_VALUE,
                "category": spec.category.value,
            }
            for spec in CANONICAL_FIELD_BY_KEY.values()
        ],
    }


def engine_output_contract_text() -> str:
    """JSON output contract shared by every 读图取数 prompt. Do not hand-copy the catalog."""
    grades = " / ".join(f"「{value}」" for value in quality_grade_values())
    example = json.dumps(engine_output_contract_example(), ensure_ascii=False, indent=2)
    catalog = "\n".join(field_catalog_lines())
    required = "、".join(ENGINE_RESULT_REQUIRED_KEYS)
    field_keys = "、".join(ENGINE_FIELD_REQUIRED_KEYS)
    return (
        "【输出契约】\n"
        "只返回一个 JSON 对象，不要 Markdown 代码围栏，不要解释文字。"
        f"对象必须恰好包含三个 key，禁止额外 key：{required}。\n"
        "\n"
        f"quality_grade：整图级图纸质量分级，必须是以下三档之一，"
        f"且只表示图纸本身的可读性，不代表结果可以免核：{grades}。\n"
        "判定：\n"
        "- 「清晰」：标题栏、尺寸与公差标注清楚可读，无严重糊、反光或裁切；"
        "规范矢量 PDF 通常属此档。\n"
        "- 「一般」：扫描件、手机拍照或微信截图，关键字段仍可辨认，但局部可能吃力。\n"
        "- 「差」：糊、过曝、反光、裁切或分辨率过低，标题栏或公差等关键信息无法可靠读取。"
        "差图仍须返回本 JSON，看不清的字段不要编造。\n"
        "\n"
        "is_assembly_or_exploded：布尔值。"
        "本图是装配图（多个零件的装配关系）或爆炸图（多零件分解展开）时为 true；"
        "是单个机加工零件的零件图时为 false。"
        "装配图与爆炸图不在处理范围；判定为 true 时 fields 仍按目录列出，"
        "value 一律为 null，不要拆件取数。\n"
        "\n"
        f"fields：数组。每一项必须恰好包含 {field_keys}，禁止额外 key。"
        "key / label / category 必须与下列字段目录逐字一致，"
        "禁止编造目录外字段，禁止改写 label 或 category。\n"
        "图上没有的字段必须出现，value 填 JSON null"
        "（不要用空字符串，不要编造看起来合理的值）。\n"
        "\n"
        "字段目录（由产品字段目录生成，禁止手抄漂移）：\n"
        f"{catalog}\n"
        "\n"
        "JSON 结构样例（图上字段皆缺失时的合法返回）：\n"
        f"{example}"
    )
