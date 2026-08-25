from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from quote_assistant.config import Settings
from quote_assistant.domain.confidentiality import (
    ConfidentialityNotice,
    DrawingStorageNotice,
    HardGateStatus,
)

ADR_0009_RELATIVE = "docs/adr/0009-mvp-multimodal-llm-vendor.md"
RESEARCH_NOTES_RELATIVE = ".scratch/mvp-quote-assistant/research/02-llm-vendor-compliance/"

_HARD_GATES = (
    ("g1_storage_in_mainland", "数据存储/处理在中国大陆"),
    ("g2_no_training", "书面承诺不用于模型训练"),
    ("g3_dpa", "可签 DPA（中国站主体、覆盖该推理 API）"),
)

_PENDING = "待填"


@dataclass(frozen=True)
class Adr0009Snapshot:
    """Structured fields copied from ADR-0009. Parser does not invent verdicts."""

    title: str
    status: str
    vendor_decision_line: str
    hard_gates: tuple[HardGateStatus, ...]
    implementation_constraints: tuple[str, ...]
    research_notes_path: str
    adr_path: str


def find_repo_file(*parts: str) -> Path:
    start = Path(__file__).resolve()
    for parent in [start, *start.parents]:
        candidate = parent.joinpath(*parts)
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("找不到 " + "/".join(parts))


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""


def _status_line(text: str) -> str:
    match = re.search(r"\*\*状态：([^*]+)\*\*", text)
    if match is None:
        return _PENDING
    return match.group(1).strip()


def _vendor_decision_line(text: str) -> str:
    after_choice = re.search(r"选用：\s*(.+)", text, flags=re.DOTALL)
    if after_choice is None:
        return _PENDING
    for line in after_choice.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("**") and stripped.endswith("**"):
            return stripped.strip("*").strip()
        if stripped.startswith("**"):
            return stripped.strip("*").strip()
    return _PENDING


def _parse_gate_table(text: str) -> tuple[HardGateStatus, ...]:
    by_name = {name: HardGateStatus(key, name, _PENDING, _PENDING) for key, name in _HARD_GATES}
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        name, verdict, evidence = cells[0], cells[1], cells[2]
        if name == "门槛" or set(name) <= {"-", ":"}:
            continue
        for key, gate_name in _HARD_GATES:
            if name == gate_name or gate_name in name:
                by_name[gate_name] = HardGateStatus(key, gate_name, verdict, evidence)
    return tuple(by_name[name] for _key, name in _HARD_GATES)


def _implementation_constraints(text: str) -> tuple[str, ...]:
    marker = "实现约束（有条件通过时必填，否则写「无」）"
    start = text.find(marker)
    if start < 0:
        return ()
    rest = text[start + len(marker) :].lstrip("：:").lstrip()
    items: list[str] = []
    for line in rest.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return tuple(items)


def parse_adr_0009_text(text: str, *, adr_path: str = ADR_0009_RELATIVE) -> Adr0009Snapshot:
    research = RESEARCH_NOTES_RELATIVE
    mentioned = re.search(r"`(\.scratch/mvp-quote-assistant/research/02-llm-vendor-compliance/)`", text)
    if mentioned is not None:
        research = mentioned.group(1)
    return Adr0009Snapshot(
        title=_first_heading(text),
        status=_status_line(text),
        vendor_decision_line=_vendor_decision_line(text),
        hard_gates=_parse_gate_table(text),
        implementation_constraints=_implementation_constraints(text),
        research_notes_path=research,
        adr_path=adr_path,
    )


def parse_adr_0009_file(path: Path) -> Adr0009Snapshot:
    return parse_adr_0009_text(path.read_text(encoding="utf-8"), adr_path=ADR_0009_RELATIVE)


def vendor_is_selected(snapshot: Adr0009Snapshot) -> bool:
    if "blocked" in snapshot.status.lower():
        return False
    if "不得把本文件读成" in snapshot.status:
        return False
    if "模板" in snapshot.title or "决定未关闭" in snapshot.title:
        return False
    line = snapshot.vendor_decision_line
    if not line or line.startswith(_PENDING):
        return False
    return True


def _gate(snapshot: Adr0009Snapshot, key: str) -> HardGateStatus:
    for gate in snapshot.hard_gates:
        if gate.key == key:
            return gate
    raise KeyError(key)


def _training_statement(snapshot: Adr0009Snapshot) -> str:
    gate = _gate(snapshot, "g2_no_training")
    if gate.verdict == _PENDING:
        return "书面不训练承诺：待填。票 02 未关闭，不得把任何供应商帮助页或口头承诺写成已落实。"
    return f"书面不训练承诺：{gate.verdict}。证据：{gate.evidence}"


def _dpa_statement(snapshot: Adr0009Snapshot) -> str:
    gate = _gate(snapshot, "g3_dpa")
    if gate.verdict == _PENDING:
        return "DPA：待填。公开条款核验的出筛集合为空；国际站 DPA 不算中国站推理 API 的可签证明。"
    return f"DPA：{gate.verdict}。证据：{gate.evidence}"


def drawing_storage_from_settings(settings: Settings) -> DrawingStorageNotice:
    backend = settings.object_store_backend.strip().lower()
    if backend == "oss":
        endpoint = settings.oss_endpoint or "未配置"
        bucket = settings.oss_bucket or "未配置"
        return DrawingStorageNotice(
            backend="oss",
            location_summary=f"阿里云 OSS（bucket={bucket}，endpoint={endpoint}）",
            notes="这是当前运行配置，不是票 02 对模型供应商处理地域的结论，也不构成「数据在中国大陆」的门槛通过证明。",
        )
    return DrawingStorageNotice(
        backend="local",
        location_summary=f"本地目录 {settings.local_object_dir}（开发/测试用，非生产 OSS）",
        notes="本地目录不是生产对象存储承诺，也不能用来回答客户「图纸存在哪一区域」。",
    )


def _processor_summary(snapshot: Adr0009Snapshot, settings: Settings) -> str:
    engine = settings.extraction_engine.strip().lower()
    if vendor_is_selected(snapshot):
        return (
            f"ADR-0009 选定处理方：{snapshot.vendor_decision_line}。"
            f"当前进程提取引擎开关为 {engine}。"
        )
    if engine == "vendor":
        return (
            "处理方尚未选定。当前进程打开了 vendor 骨架，但仍拒绝调用付费 API"
            "（票 02 / ADR-0009 仍为模板）。"
        )
    return (
        "处理方尚未选定。当前默认提取引擎是 fixture 假实现，"
        "不把零件图发给第三方多模态大模型。"
    )


def _ticket_02_status(snapshot: Adr0009Snapshot) -> str:
    if vendor_is_selected(snapshot):
        return "票 02 已关闭；本页字段来自已关闭的 ADR-0009。"
    return (
        "票 02 未关闭。ADR-0009 仍是模板，决定未填写。"
        "公开条款核验的出筛集合为空（见调研笔记）。"
        "不得把任何候选写成已选定供应商。"
    )


def compose_confidentiality_notice(
    snapshot: Adr0009Snapshot,
    settings: Settings,
) -> ConfidentialityNotice:
    selected = vendor_is_selected(snapshot)
    caveats = (
        "本页只陈述当前可核对事实，不构成供应商承诺或营销文案。",
        "三条硬门槛的判定必须来自 ADR-0009；待填格子保持待填。",
        f"调研原文：{snapshot.research_notes_path}",
        f"ADR 原文：{snapshot.adr_path}",
    )
    return ConfidentialityNotice(
        ticket_02_closed=selected,
        ticket_02_status=_ticket_02_status(snapshot),
        adr_status=snapshot.status,
        adr_path=snapshot.adr_path,
        research_notes_path=snapshot.research_notes_path,
        vendor_selected=selected,
        selected_vendor=snapshot.vendor_decision_line if selected else None,
        vendor_decision_line=snapshot.vendor_decision_line,
        hard_gates=snapshot.hard_gates,
        implementation_constraints=snapshot.implementation_constraints,
        drawing_storage=drawing_storage_from_settings(settings),
        processor_summary=_processor_summary(snapshot, settings),
        current_extraction_engine=settings.extraction_engine.strip().lower(),
        used_for_training_statement=_training_statement(snapshot),
        dpa_statement=_dpa_statement(snapshot),
        caveats=caveats,
    )


class Adr0009ConfidentialitySource:
    """Load the admin 保密说明 from ADR-0009 on disk plus current runtime settings."""

    def __init__(self, settings: Settings, adr_path: Path | None = None) -> None:
        self._settings = settings
        self._adr_path = adr_path

    def load(self) -> ConfidentialityNotice:
        path = self._adr_path or find_repo_file(*ADR_0009_RELATIVE.split("/"))
        snapshot = parse_adr_0009_file(path)
        return compose_confidentiality_notice(snapshot, self._settings)
