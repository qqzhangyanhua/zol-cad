from __future__ import annotations

import json
import logging

from quote_assistant.adapter.extraction.fixtures import DIRTY_ENGINE_PAYLOAD
from quote_assistant.adapter.extraction.validation import (
    ADAPTER_VALIDATION_FAILED_REASON,
    parse_engine_result,
    summarize_engine_payload,
)
from quote_assistant.domain.engine_output_contract import (
    ENGINE_ABSENT_FIELD_VALUE,
    ENGINE_RESULT_REQUIRED_KEYS,
    engine_output_contract_example,
    engine_output_contract_text,
    field_catalog_lines,
    quality_grade_values,
)
from quote_assistant.domain.errors import ExtractionValidationFailed
from quote_assistant.domain.extraction import CANONICAL_FIELD_BY_KEY
from quote_assistant.domain.part_family import (
    PROVISIONAL_OTHER_PART_FAMILY_ID,
    TARGET_PART_FAMILY_ID,
    UNKNOWN_PART_FAMILY_ID,
)
from quote_assistant.domain.prompt_templates import prompt_template_for
from quote_assistant.domain.quality import QualityGrade


def _json_example_from_prompt(body: str) -> dict[str, object]:
    marker = "JSON 结构样例"
    start = body.index(marker)
    return json.loads(body[body.index("{", start) :])


def test_字段目录只有一份来源提示词清单由CANONICAL_FIELD_BY_KEY生成() -> None:
    lines = field_catalog_lines()
    assert len(lines) == len(CANONICAL_FIELD_BY_KEY)
    for spec, line in zip(CANONICAL_FIELD_BY_KEY.values(), lines, strict=True):
        assert spec.key in line
        assert spec.label in line
        assert spec.category.value in line
    contract = engine_output_contract_text()
    for line in lines:
        assert line in contract
    target = prompt_template_for(TARGET_PART_FAMILY_ID).body
    generic = prompt_template_for(UNKNOWN_PART_FAMILY_ID).body
    other = prompt_template_for(PROVISIONAL_OTHER_PART_FAMILY_ID).body
    assert contract in target
    assert contract in generic
    assert contract in other
    assert generic == other


def test_提示词包含完整输出契约与质量分级装配图判定及留空约定() -> None:
    contract = engine_output_contract_text()
    for key in ENGINE_RESULT_REQUIRED_KEYS:
        assert key in contract
    assert "JSON" in contract
    for grade in quality_grade_values():
        assert f"「{grade}」" in contract
    assert set(quality_grade_values()) == {grade.value for grade in QualityGrade}
    assert "is_assembly_or_exploded" in contract
    assert "装配图" in contract
    assert "爆炸图" in contract
    assert "JSON null" in contract
    assert "不要用空字符串" in contract
    assert ENGINE_ABSENT_FIELD_VALUE is None
    for family_id in (TARGET_PART_FAMILY_ID, UNKNOWN_PART_FAMILY_ID):
        body = prompt_template_for(family_id).body
        assert contract in body
        assert "quality_grade" in body
        assert "is_assembly_or_exploded" in body


def test_符合提示词契约的样例payload能通过适配器校验() -> None:
    payload = engine_output_contract_example()
    result = parse_engine_result(payload)
    assert result.quality_grade is QualityGrade.CLEAR
    assert result.is_assembly_or_exploded is False
    assert [field.key for field in result.fields] == list(CANONICAL_FIELD_BY_KEY)
    for field in result.fields:
        spec = CANONICAL_FIELD_BY_KEY[field.key]
        assert field.label == spec.label
        assert field.category == spec.category
        assert field.value is None

    filled = engine_output_contract_example()
    fields = filled["fields"]
    assert isinstance(fields, list)
    drawing_no = next(item for item in fields if item["key"] == "drawing_no")
    drawing_no["value"] = "FL-001"
    parsed = parse_engine_result(filled)
    by_key = {field.key: field for field in parsed.fields}
    assert by_key["drawing_no"].value == "FL-001"
    assert by_key["material"].value is None


def test_提示词正文里的JSON样例本身能通过适配器校验() -> None:
    for family_id in (TARGET_PART_FAMILY_ID, UNKNOWN_PART_FAMILY_ID):
        embedded = _json_example_from_prompt(prompt_template_for(family_id).body)
        assert embedded == engine_output_contract_example()
        parsed = parse_engine_result(embedded)
        assert parsed.quality_grade is QualityGrade.CLEAR
        assert all(field.value is None for field in parsed.fields)


def test_校验失败留下结构摘要且不含图像内容(caplog) -> None:
    image_blob = "iVBORw0KGgoAAAANSUhEUgAAAAEUNIQUE-IMAGE-BYTES"
    dirty = {
        **DIRTY_ENGINE_PAYLOAD,
        "image_base64": image_blob,
        "page_content": b"\x89PNG-not-a-real-image",
    }
    logger = logging.getLogger("quote_assistant.extraction.validation")
    with caplog.at_level(logging.WARNING, logger=logger.name):
        try:
            parse_engine_result(dirty)
        except ExtractionValidationFailed as exc:
            assert str(exc) == ADAPTER_VALIDATION_FAILED_REASON
            assert exc.diagnostic is not None
            assert "keys=" in exc.diagnostic
            assert "extra_keys=" in exc.diagnostic
            assert "image_base64" in exc.diagnostic
            assert "omitted_image_keys=" in exc.diagnostic
            assert "fields=len=1" in exc.diagnostic
            assert "value_type=int" in exc.diagnostic
            assert image_blob not in exc.diagnostic
            assert "UNIQUE-IMAGE-BYTES" not in exc.diagnostic
            captured = caplog.text + "".join(record.getMessage() for record in caplog.records)
            assert "engine_payload_validation_failed" in captured
            assert exc.diagnostic in captured
            assert image_blob not in captured
            assert "UNIQUE-IMAGE-BYTES" not in captured
            return
    raise AssertionError("脏载荷应被适配器拒绝")


def test_结构摘要不落原始字节或超长字符串() -> None:
    summary = summarize_engine_payload(
        {
            "quality_grade": "清晰",
            "is_assembly_or_exploded": False,
            "image": "A" * 400,
            "fields": "not-a-list",
        }
    )
    assert "keys=" in summary
    assert "quality_grade='清晰'" in summary or 'quality_grade="清晰"' in summary
    assert "image" in summary
    assert "A" * 20 not in summary
    assert "fields=type=str" in summary
