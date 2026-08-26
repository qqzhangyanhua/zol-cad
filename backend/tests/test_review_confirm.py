from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, login

HIGH_RISK_KEYS = ("tightest_tolerance", "max_envelope", "deepest_hole", "thinnest_wall")
LOW_RISK_KEYS = ("drawing_no", "part_name", "material", "quantity")


def _upload(client: TestClient, filename: str) -> dict:
    response = client.post(
        "/part-drawings",
        files=[("files", (filename, PNG_1X1, "image/png"))],
    )
    assert response.status_code == 200
    return response.json()["items"][0]


def _login_quoter(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200


def _fields_by_key(item: dict) -> dict[str, dict]:
    return {field["key"]: field for field in item["extracted_fields"]}


def _confirm(client: TestClient, drawing_id: str, field_key: str):
    return client.post(f"/part-drawings/{drawing_id}/fields/{field_key}/confirm")


def _complete(client: TestClient, drawing_id: str):
    return client.post(f"/part-drawings/{drawing_id}/complete-review")


def test_清晰图上尺寸与公差仍需确认低风险字段不强制(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TQ-01.png")
    assert item["quality_grade"] == "清晰"
    fields = _fields_by_key(item)

    for key in HIGH_RISK_KEYS:
        assert fields[key]["requires_confirmation"] is True
        assert fields[key]["confirmed"] is False
    for key in LOW_RISK_KEYS:
        assert fields[key]["requires_confirmation"] is False

    assert item["pending_confirmation_count"] == 4
    assert item["pending_confirmation_labels"] == ["最严公差", "最大外形", "最深孔", "最薄壁"]


def test_尺寸与公差在清晰一般差三档都需确认(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    clear = _upload(client, "FX-TQ-01.png")
    average = _upload(client, "FX-TA-01.png")
    poor = _upload(client, "FX-TP-01.png")
    continued = client.post(f"/part-drawings/{poor['id']}/continue-despite-quality")
    assert continued.status_code == 200
    poor_extracted = continued.json()

    for item in (clear, average, poor_extracted):
        fields = _fields_by_key(item)
        for key in HIGH_RISK_KEYS:
            assert fields[key]["requires_confirmation"] is True
            assert fields[key]["confirmed"] is False

    average_fields = _fields_by_key(average)
    poor_fields = _fields_by_key(poor_extracted)
    for key in LOW_RISK_KEYS:
        assert average_fields[key]["requires_confirmation"] is True
        assert poor_fields[key]["requires_confirmation"] is True


def test_存在未处理需确认项时无法标记已复核并说明还差哪些(
    client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TQ-01.png")
    blocked = _complete(client, item["id"])
    assert blocked.status_code == 409
    detail = blocked.json()["detail"]
    assert "还不能标记已复核" in detail
    assert "最严公差" in detail
    assert "最大外形" in detail
    assert "最深孔" in detail
    assert "最薄壁" in detail
    assert client.get(f"/part-drawings/{item['id']}").json()["status"] == "已提取"


def test_逐项确认后可标记已复核并写入带时间戳的事件(
    client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TQ-01.png")
    drawing_id = item["id"]

    for key in HIGH_RISK_KEYS:
        confirmed = _confirm(client, drawing_id, key)
        assert confirmed.status_code == 200
        body = confirmed.json()
        assert body["status"] == "复核中"
        assert _fields_by_key(body)[key]["confirmed"] is True

    mid = client.get(f"/part-drawings/{drawing_id}").json()
    assert mid["pending_confirmation_count"] == 0
    assert mid["pending_confirmation_labels"] == []

    done = _complete(client, drawing_id)
    assert done.status_code == 200
    assert done.json()["status"] == "已复核"

    events = client.get(f"/part-drawings/{drawing_id}/events").json()["items"]
    assert [row["to_status"] for row in events][-2:] == ["复核中", "已复核"]
    reviewed = events[-1]
    assert reviewed["occurred_at"]
    assert reviewed["sequence_no"] >= 6


def test_就地修改自动保存刷新后仍在(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TQ-01.png")
    drawing_id = item["id"]

    patched = client.patch(
        f"/part-drawings/{drawing_id}/fields/tightest_tolerance",
        json={"value": "IT6"},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "复核中"
    field = _fields_by_key(patched.json())["tightest_tolerance"]
    assert field["value"] == "IT6"
    assert field["confirmed"] is True
    assert field["requires_confirmation"] is True

    refreshed = client.get(f"/part-drawings/{drawing_id}").json()
    saved = _fields_by_key(refreshed)["tightest_tolerance"]
    assert refreshed["status"] == "复核中"
    assert saved["value"] == "IT6"
    assert saved["confirmed"] is True
    assert "IT6" not in refreshed["pending_confirmation_labels"]
    assert "最严公差" not in refreshed["pending_confirmation_labels"]
    assert refreshed["pending_confirmation_count"] == 3
