from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_admin, create_factory, create_quoter, login
from quote_assistant.domain.correction import CORRECTION_STATS_PURPOSE


FORBIDDEN_COPY = ("越用越准", "自动学习", "实时优化", "越改越准")
REPO_ROOT = Path(__file__).resolve().parents[2]


def _upload(client: TestClient, filename: str) -> dict:
    response = client.post(
        "/part-drawings",
        files=[("files", (filename, PNG_1X1, "image/png"))],
    )
    assert response.status_code == 200
    return response.json()["items"][0]


def _login_quoter(client: TestClient, db_session: Session, username: str = "quoter_a") -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, username, "secret-a")
    create_admin(db_session, factory_id, "admin_a", "secret-admin")
    db_session.commit()
    assert login(client, username, "secret-a").status_code == 200


def test_修正一个值后能读到原值与新值都正确的记录(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TQ-01.png")
    drawing_id = item["id"]
    original = next(
        field["value"] for field in item["extracted_fields"] if field["key"] == "tightest_tolerance"
    )
    assert original == "IT7"

    patched = client.patch(
        f"/part-drawings/{drawing_id}/fields/tightest_tolerance",
        json={"value": "IT6"},
    )
    assert patched.status_code == 200

    records = client.get(f"/part-drawings/{drawing_id}/correction-records")
    assert records.status_code == 200
    items = records.json()["items"]
    assert len(items) == 1
    record = items[0]
    assert record["field_key"] == "tightest_tolerance"
    assert record["field_type"] == "最严公差"
    assert record["old_value"] == "IT7"
    assert record["new_value"] == "IT6"
    assert record["part_drawing_id"] == drawing_id
    assert record["actor_user_id"]
    assert record["occurred_at"]


def test_同一字段多次修改产生多条不可被覆盖的记录(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TQ-01.png")
    drawing_id = item["id"]

    assert (
        client.patch(
            f"/part-drawings/{drawing_id}/fields/tightest_tolerance",
            json={"value": "IT6"},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/part-drawings/{drawing_id}/fields/tightest_tolerance",
            json={"value": "IT5"},
        ).status_code
        == 200
    )

    items = client.get(f"/part-drawings/{drawing_id}/correction-records").json()["items"]
    assert len(items) == 2
    assert items[0]["old_value"] == "IT7"
    assert items[0]["new_value"] == "IT6"
    assert items[1]["old_value"] == "IT6"
    assert items[1]["new_value"] == "IT5"
    assert items[0]["id"] != items[1]["id"]


def test_手工补录产生原值为空的修正记录(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TQ-01.png")
    drawing_id = item["id"]
    assert next(field["value"] for field in item["extracted_fields"] if field["key"] == "deepest_hole") is None

    added = client.post(
        f"/part-drawings/{drawing_id}/fields",
        json={"kind": "deepest_hole", "value": "Ø8×48"},
    )
    assert added.status_code == 200

    extra = client.post(
        f"/part-drawings/{drawing_id}/fields",
        json={"kind": "tightest_tolerance", "value": "IT6", "label": "另一处严公差"},
    )
    assert extra.status_code == 200

    items = client.get(f"/part-drawings/{drawing_id}/correction-records").json()["items"]
    assert len(items) == 2
    filled = next(record for record in items if record["field_key"] == "deepest_hole")
    assert filled["old_value"] is None
    assert filled["new_value"] == "Ø8×48"
    assert filled["field_type"] == "最深孔"
    extra_record = next(
        record for record in items if record["field_key"] == "tightest_tolerance__added__1"
    )
    assert extra_record["old_value"] is None
    assert extra_record["new_value"] == "IT6"
    assert extra_record["field_type"] == "最严公差"


def test_管理员能按字段类型看到本厂修正频次报价员被拒绝(
    client: TestClient, db_session: Session
) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    create_admin(db_session, factory_id, "admin_a", "secret-admin")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200
    item = _upload(client, "FX-TQ-01.png")
    drawing_id = item["id"]
    assert (
        client.patch(
            f"/part-drawings/{drawing_id}/fields/tightest_tolerance",
            json={"value": "IT6"},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/part-drawings/{drawing_id}/fields/tightest_tolerance",
            json={"value": "IT5"},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/part-drawings/{drawing_id}/fields/drawing_no",
            json={"value": "FL-009"},
        ).status_code
        == 200
    )

    forbidden = client.get("/correction-stats")
    assert forbidden.status_code == 403
    assert "管理员" in forbidden.json()["detail"]

    client.post("/auth/logout")
    assert login(client, "admin_a", "secret-admin").status_code == 200
    stats = client.get("/correction-stats")
    assert stats.status_code == 200
    body = stats.json()
    assert body["purpose"] == CORRECTION_STATS_PURPOSE
    assert "越用越准" not in body["purpose"]
    assert "自动学习" not in body["purpose"]
    by_type = {row["field_type"]: row["correction_count"] for row in body["items"]}
    assert by_type["最严公差"] == 2
    assert by_type["图号"] == 1


def test_甲厂报价员读不到乙厂的修正记录(client: TestClient, db_session: Session) -> None:
    factory_a = create_factory(db_session, "华东精密")
    factory_b = create_factory(db_session, "南方模具")
    create_quoter(db_session, factory_a, "quoter_a", "secret-a")
    create_quoter(db_session, factory_b, "quoter_b", "secret-b")
    create_admin(db_session, factory_a, "admin_a", "secret-admin-a")
    create_admin(db_session, factory_b, "admin_b", "secret-admin-b")
    db_session.commit()

    assert login(client, "quoter_b", "secret-b").status_code == 200
    item = _upload(client, "FX-TQ-01.png")
    drawing_id = item["id"]
    assert (
        client.patch(
            f"/part-drawings/{drawing_id}/fields/tightest_tolerance",
            json={"value": "IT6"},
        ).status_code
        == 200
    )
    own = client.get(f"/part-drawings/{drawing_id}/correction-records")
    assert own.status_code == 200
    assert len(own.json()["items"]) == 1

    client.post("/auth/logout")
    assert login(client, "quoter_a", "secret-a").status_code == 200
    assert client.get(f"/part-drawings/{drawing_id}/correction-records").status_code == 404

    client.post("/auth/logout")
    assert login(client, "admin_a", "secret-admin-a").status_code == 200
    stats_a = client.get("/correction-stats")
    assert stats_a.status_code == 200
    assert stats_a.json()["items"] == []
    assert client.get(f"/part-drawings/{drawing_id}/correction-records").status_code == 404

    client.post("/auth/logout")
    assert login(client, "admin_b", "secret-admin-b").status_code == 200
    stats_b = client.get("/correction-stats")
    assert stats_b.status_code == 200
    by_type = {row["field_type"]: row["correction_count"] for row in stats_b.json()["items"]}
    assert by_type == {"最严公差": 1}


def test_界面与用途文案不暗示实时模型优化() -> None:
    sources: list[str] = []
    for path in (REPO_ROOT / "frontend" / "src").rglob("*"):
        if path.suffix in {".ts", ".tsx"}:
            sources.append(path.read_text(encoding="utf-8"))
    backend = REPO_ROOT / "backend" / "src" / "quote_assistant"
    for path in backend.rglob("*.py"):
        sources.append(path.read_text(encoding="utf-8"))
    blob = "\n".join(sources)
    for phrase in FORBIDDEN_COPY:
        assert phrase not in blob
    assert CORRECTION_STATS_PURPOSE in blob
    assert "闭源" in CORRECTION_STATS_PURPOSE
