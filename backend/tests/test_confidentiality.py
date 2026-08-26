from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from helpers import create_admin, create_factory, create_quoter, login
from quote_assistant.adapter.confidentiality.adr0009 import (
    ADR_0009_RELATIVE,
    RESEARCH_NOTES_RELATIVE,
    Adr0009ConfidentialitySource,
    compose_confidentiality_notice,
    find_repo_file,
    load_bundled_adr_0009,
    parse_adr_0009_file,
    parse_adr_0009_text,
    vendor_is_selected,
)
from quote_assistant.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"


CLOSED_ADR = """# MVP 多模态大模型供应商

**状态：已决定 — 仅供解析器回归，不是生产选定。**

调研产出：`.scratch/mvp-quote-assistant/research/02-llm-vendor-compliance/`

## 决定

MVP 生产环境的提取引擎（ADR-0003 的可替换 Port）选用：

**示例供应商 / 示例产品 / 示例型号 / 华北2（北京） / 按量**

## 三条门槛各自的证据

| 门槛 | 判定 | 证据（URL + 引文或回函） |
|------|------|--------------------------|
| 数据存储/处理在中国大陆 | 通过 | https://example.invalid/g1 |
| 书面承诺不用于模型训练 | 通过 | https://example.invalid/g2 |
| 可签 DPA（中国站主体、覆盖该推理 API） | 通过 | https://example.invalid/g3 |

实现约束（有条件通过时必填，否则写「无」）：

- 锁定地域 / endpoint：华北2（北京）
- 禁止使用的 SKU（如 Coding Plan、个人版、境外地域）：Coding Plan
- 禁止签署的除外协议（如数据授权用于训练）：数据授权使用协议
"""


def _login_admin(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_admin(db_session, factory_id, "admin_a", "secret-admin")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "admin_a", "secret-admin").status_code == 200


def test_打包ADR与仓库原文一致且不依赖源树() -> None:
    live = find_repo_file(*ADR_0009_RELATIVE.split("/")).read_text(encoding="utf-8")
    assert load_bundled_adr_0009() == live
    notice = Adr0009ConfidentialitySource(Settings(extraction_engine="fixture")).load()
    assert notice.vendor_selected is False
    assert notice.adr_path == ADR_0009_RELATIVE


def test_当前ADR解析为未选定且三条门槛待填() -> None:
    snapshot = parse_adr_0009_file(find_repo_file(*ADR_0009_RELATIVE.split("/")))
    assert vendor_is_selected(snapshot) is False
    assert snapshot.vendor_decision_line.startswith("待填")
    assert [gate.verdict for gate in snapshot.hard_gates] == ["待填", "待填", "待填"]
    assert snapshot.research_notes_path == RESEARCH_NOTES_RELATIVE
    assert snapshot.implementation_constraints == (
        "锁定地域 / endpoint：待填",
        "禁止使用的 SKU（如 Coding Plan、个人版、境外地域）：待填",
        "禁止签署的除外协议（如数据授权用于训练）：待填",
    )


def test_ADR关闭后保密说明改为读入选定供应商() -> None:
    snapshot = parse_adr_0009_text(CLOSED_ADR, adr_path=ADR_0009_RELATIVE)
    assert vendor_is_selected(snapshot) is True
    notice = compose_confidentiality_notice(snapshot, Settings(extraction_engine="fixture"))
    assert notice.ticket_02_closed is True
    assert notice.selected_vendor is not None
    assert "示例供应商" in notice.selected_vendor
    assert notice.hard_gates[0].verdict == "通过"
    assert "https://example.invalid/g2" in notice.used_for_training_statement
    assert "https://example.invalid/g3" in notice.dpa_statement


def test_管理员能看到诚实的保密说明报价员不能(
    client: TestClient, db_session: Session
) -> None:
    _login_admin(client, db_session)
    response = client.get("/admin/confidentiality")
    assert response.status_code == 200
    body = response.json()
    assert body["ticket_02_closed"] is False
    assert body["vendor_selected"] is False
    assert body["selected_vendor"] is None
    assert body["vendor_decision_line"].startswith("待填")
    assert "票 02 未关闭" in body["ticket_02_status"]
    assert "出筛集合为空" in body["ticket_02_status"]
    assert body["adr_path"] == ADR_0009_RELATIVE
    assert body["research_notes_path"] == RESEARCH_NOTES_RELATIVE
    assert body["current_extraction_engine"] == "fixture"
    assert "fixture 假实现" in body["processor_summary"]
    assert "不把零件图发给第三方" in body["processor_summary"]
    assert body["drawing_storage"]["backend"] == "local"
    assert "本地目录" in body["drawing_storage"]["location_summary"]
    assert "不是生产对象存储承诺" in body["drawing_storage"]["notes"]
    names = [gate["name"] for gate in body["hard_gates"]]
    assert names == [
        "数据存储/处理在中国大陆",
        "书面承诺不用于模型训练",
        "可签 DPA（中国站主体、覆盖该推理 API）",
    ]
    assert all(gate["verdict"] == "待填" for gate in body["hard_gates"])
    assert body["implementation_constraints"][0].endswith("待填")
    assert "待填" in body["used_for_training_statement"]
    assert "待填" in body["dpa_statement"]
    assert "不构成供应商承诺或营销文案" in body["caveats"][0]
    assert "已签署 DPA" not in response.text
    assert "数据保证在中国大陆" not in response.text

    client.post("/auth/logout")
    assert login(client, "quoter_a", "secret-a").status_code == 200
    assert client.get("/admin/confidentiality").status_code == 403


def test_面向客户的保密与风险文案不暴露内部追踪标识() -> None:
    notice = (FRONTEND_SRC / "components" / "ConfidentialityNotice.tsx").read_text(encoding="utf-8")
    catalog = (FRONTEND_SRC / "components" / "RiskRuleCatalog.tsx").read_text(encoding="utf-8")
    for blob, name in ((notice, "ConfidentialityNotice"), (catalog, "RiskRuleCatalog")):
        assert "票 0" not in blob, name
        assert "ADR-000" not in blob, name
        assert ".scratch" not in blob, name
        assert "adr_path" not in blob, name
        assert "research_notes_path" not in blob, name
    assert "presentConfidentialityNotice" in notice
    assert "presentRiskRuleDescription" in catalog
    assert "阈值仍是暂定值" in catalog


def test_管理员侧栏能点进全厂处理记录与保密说明() -> None:
    sidebar = (FRONTEND_SRC / "components" / "AppSidebar.tsx").read_text(encoding="utf-8")
    assert 'href: "/admin/processing-records"' in sidebar
    assert 'href: "/admin/confidentiality"' in sidebar
    assert "全厂处理记录" in sidebar
    assert "保密说明" in sidebar
