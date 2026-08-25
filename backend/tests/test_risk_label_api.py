from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, login
from quote_assistant.domain.risk_labels import NO_JUDGABLE_RISK_ITEMS_MESSAGE


def _login_quoter(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200


def _upload(client: TestClient, filename: str) -> dict:
    response = client.post(
        "/part-drawings",
        files=[("files", (filename, PNG_1X1, "image/png"))],
    )
    assert response.status_code == 200
    return response.json()["items"][0]


def test_风险标签从提取结果一路算到API返回(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    uploaded = _upload(client, "WIRE-RL-01.png")

    assert uploaded["status"] == "已提取"
    assert uploaded["extracted_fields"]
    by_key = {field["key"]: field["value"] for field in uploaded["extracted_fields"]}
    assert by_key["tightest_tolerance"] == "IT6"
    assert by_key["deepest_hole"] == "Ø8×48"
    assert by_key["thinnest_wall"] == "1.5"
    assert by_key["max_envelope"] == "Ø10×120"

    labels = uploaded["risk_labels"]
    by_rule = {label["rule_id"]: label for label in labels}
    assert set(by_rule) == {"RL-HIGH-PREC", "RL-DEEP-HOLE", "RL-THIN-WALL", "RL-SLENDER"}
    assert by_rule["RL-HIGH-PREC"]["name"] == "高精度"
    assert by_rule["RL-HIGH-PREC"]["triggering_value"] == "IT6"
    assert "IT6" in by_rule["RL-HIGH-PREC"]["reason"]
    assert by_rule["RL-DEEP-HOLE"]["name"] == "深孔"
    assert by_rule["RL-DEEP-HOLE"]["triggering_value"] == "Ø8×48"
    assert by_rule["RL-THIN-WALL"]["name"] == "薄壁"
    assert by_rule["RL-THIN-WALL"]["triggering_value"] == "1.5"
    assert by_rule["RL-SLENDER"]["name"] == "细长"
    assert by_rule["RL-SLENDER"]["triggering_value"] == "Ø10×120"
    assert uploaded["no_judgable_risk_message"] == NO_JUDGABLE_RISK_ITEMS_MESSAGE

    reread = client.get(f"/part-drawings/{uploaded['id']}")
    assert reread.status_code == 200
    assert reread.json()["risk_labels"] == labels


def test_未触发风险标签时API给出空列表与固定空态文案(
    client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TQ-01.png")
    assert item["status"] == "已提取"
    assert item["risk_labels"] == []
    assert item["no_judgable_risk_message"] == "未发现可判定的风险项，不代表此件无风险"
    listed = client.get("/part-drawings").json()["items"][0]
    assert listed["risk_labels"] == []
    assert listed["no_judgable_risk_message"] == NO_JUDGABLE_RISK_ITEMS_MESSAGE
