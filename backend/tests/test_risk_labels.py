from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from quote_assistant.domain.extraction import CANONICAL_FIELD_BY_KEY, ExtractedField
from quote_assistant.domain.risk_labels import (
    FORBIDDEN_RISK_LABEL_SEMANTICS,
    RISK_LABEL_VOCABULARY,
    RiskLabelName,
    evaluate_risk_labels,
)

DOMAIN_RISK = (
    Path(__file__).resolve().parents[1] / "src" / "quote_assistant" / "domain" / "risk_labels.py"
)


def _field(key: str, value: str | None) -> ExtractedField:
    spec = CANONICAL_FIELD_BY_KEY[key]
    return ExtractedField(spec.key, spec.label, value, spec.category)


def _fields(**values: str | None) -> tuple[ExtractedField, ...]:
    return tuple(_field(key, value) for key, value in values.items())


def _fired_rule_ids(fields: tuple[ExtractedField, ...]) -> set[str]:
    return {label.rule_id for label in evaluate_risk_labels(fields)}


# 每条规则：刚好触发 / 刚好不触发 / 边界值。阈值均为暂定（待票 01）。
RULE_CASES: list[tuple[str, str, dict[str, str], bool]] = [
    ("RL-HIGH-PREC", "刚好触发", {"tightest_tolerance": "IT6"}, True),
    ("RL-HIGH-PREC", "刚好不触发", {"tightest_tolerance": "IT7"}, False),
    ("RL-HIGH-PREC", "边界值", {"tightest_tolerance": "IT6"}, True),
    ("RL-DEEP-HOLE", "刚好触发", {"deepest_hole": "Ø10×51"}, True),
    ("RL-DEEP-HOLE", "刚好不触发", {"deepest_hole": "Ø10×50"}, False),
    ("RL-DEEP-HOLE", "边界值", {"deepest_hole": "Ø10×50"}, False),
    ("RL-THIN-WALL", "刚好触发", {"thinnest_wall": "2"}, True),
    ("RL-THIN-WALL", "刚好不触发", {"thinnest_wall": "2.1"}, False),
    ("RL-THIN-WALL", "边界值", {"thinnest_wall": "2"}, True),
    ("RL-SLENDER", "刚好触发", {"max_envelope": "Ø10×101"}, True),
    ("RL-SLENDER", "刚好不触发", {"max_envelope": "Ø10×100"}, False),
    ("RL-SLENDER", "边界值", {"max_envelope": "Ø10×100"}, False),
]


@pytest.mark.parametrize(
    ("rule_id", "case", "values", "should_fire"),
    RULE_CASES,
    ids=[f"{rule_id}-{case}" for rule_id, case, _values, _fire in RULE_CASES],
)
def test_每条规则刚好触发刚好不触发与边界值(
    rule_id: str, case: str, values: dict[str, str], should_fire: bool
) -> None:
    del case
    fired = _fired_rule_ids(_fields(**values))
    if should_fire:
        assert rule_id in fired
    else:
        assert rule_id not in fired


def test_输出词表不含安全无风险通过语义() -> None:
    assert RISK_LABEL_VOCABULARY == frozenset(RiskLabelName)
    for name in RISK_LABEL_VOCABULARY:
        for token in FORBIDDEN_RISK_LABEL_SEMANTICS:
            assert token not in name.value
            assert token not in name.name


def test_任意输入的输出名称都在词表内且无安全语义() -> None:
    samples = [
        _fields(),
        _fields(tightest_tolerance="IT6", deepest_hole="Ø8×48", thinnest_wall="1.5", max_envelope="Ø10×120"),
        _fields(tightest_tolerance="无风险", deepest_hole="安全", thinnest_wall="通过", max_envelope="合格"),
        _fields(tightest_tolerance="IT0", deepest_hole="见技术要求", thinnest_wall="薄", max_envelope="Ø120"),
    ]
    for fields in samples:
        for label in evaluate_risk_labels(fields):
            assert label.name in RISK_LABEL_VOCABULARY
            for token in FORBIDDEN_RISK_LABEL_SEMANTICS:
                assert token not in label.name.value
                assert token not in label.reason


def test_同一输入重复调用结果完全一致() -> None:
    fields = _fields(
        tightest_tolerance="IT6",
        deepest_hole="Ø8×48",
        thinnest_wall="1.5",
        max_envelope="Ø10×120",
    )
    first = evaluate_risk_labels(fields)
    assert first
    for _ in range(20):
        assert evaluate_risk_labels(fields) == first


def test_引擎签名只有结构化数据且源码无IO随机时间() -> None:
    assert list(inspect.signature(evaluate_risk_labels).parameters) == ["fields"]
    tree = ast.parse(DOMAIN_RISK.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint({"datetime", "random", "time", "os", "pathlib", "uuid", "secrets"})


def test_缺失或无法判定的值不触发且空列表就是空() -> None:
    assert evaluate_risk_labels(_fields()) == ()
    assert evaluate_risk_labels(_fields(tightest_tolerance=None, deepest_hole=None)) == ()
    assert evaluate_risk_labels(_fields(tightest_tolerance="见技术要求")) == ()
    assert evaluate_risk_labels(_fields(deepest_hole="Ø8")) == ()
    assert evaluate_risk_labels(_fields(max_envelope="Ø120")) == ()
    assert evaluate_risk_labels(_fields(thinnest_wall="薄")) == ()


def test_每个标签携带规则标识触发值与理由() -> None:
    labels = evaluate_risk_labels(
        _fields(
            tightest_tolerance="IT5",
            deepest_hole="Ø8×48",
            thinnest_wall="1.5mm",
            max_envelope="Ø10×120",
        )
    )
    by_id = {label.rule_id: label for label in labels}
    assert set(by_id) == {"RL-HIGH-PREC", "RL-DEEP-HOLE", "RL-THIN-WALL", "RL-SLENDER"}
    assert by_id["RL-HIGH-PREC"].name is RiskLabelName.HIGH_PRECISION
    assert by_id["RL-HIGH-PREC"].triggering_value == "IT5"
    assert "IT5" in by_id["RL-HIGH-PREC"].reason
    assert by_id["RL-DEEP-HOLE"].triggering_value == "Ø8×48"
    assert "6.00" in by_id["RL-DEEP-HOLE"].reason
    assert by_id["RL-THIN-WALL"].triggering_value == "1.5mm"
    assert by_id["RL-SLENDER"].triggering_value == "Ø10×120"
    assert [label.name for label in labels] == [
        RiskLabelName.HIGH_PRECISION,
        RiskLabelName.DEEP_HOLE,
        RiskLabelName.THIN_WALL,
        RiskLabelName.SLENDER,
    ]
