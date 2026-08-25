from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_admin, create_factory, create_quoter, login


def _upload(client: TestClient, filename: str) -> dict:
    response = client.post(
        "/part-drawings",
        files=[("files", (filename, PNG_1X1, "image/png"))],
    )
    assert response.status_code == 200
    return response.json()["items"][0]


def _switch(client: TestClient, username: str, password: str) -> None:
    client.post("/auth/logout")
    assert login(client, username, password).status_code == 200


def test_报价员读不到同厂其他报价员的零件图与报价任务管理员读得到(
    client: TestClient, db_session: Session
) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    create_quoter(db_session, factory_id, "quoter_c", "secret-c")
    create_admin(db_session, factory_id, "admin_a", "secret-admin")
    db_session.commit()

    assert login(client, "quoter_a", "secret-a").status_code == 200
    drawing_a = _upload(client, "甲报价员-轴.pdf")
    task_a = client.post(
        "/quote-tasks", json={"name": "甲的询价", "customer_name": "甲客户"}
    )
    assert task_a.status_code == 200
    assigned = client.post(
        f"/quote-tasks/{task_a.json()['id']}/part-drawings",
        json={"part_drawing_id": drawing_a["id"]},
    )
    assert assigned.status_code == 200

    _switch(client, "quoter_c", "secret-c")
    assert client.get("/part-drawings").json() == {"items": []}
    assert client.get(f"/part-drawings/{drawing_a['id']}").status_code == 404
    assert client.get(f"/part-drawings/{drawing_a['id']}/original").status_code == 404
    assert client.get("/quote-tasks").json() == {"items": []}
    assert client.get(f"/quote-tasks/{task_a.json()['id']}").status_code == 404
    assert (
        client.post(
            f"/quote-tasks/{task_a.json()['id']}/part-drawings",
            json={"part_drawing_id": drawing_a["id"]},
        ).status_code
        == 404
    )

    drawing_c = _upload(client, "丙报价员-套.pdf")
    task_c = client.post(
        "/quote-tasks", json={"name": "丙的询价", "customer_name": "丙客户"}
    )
    assert task_c.status_code == 200

    _switch(client, "admin_a", "secret-admin")
    drawings = client.get("/part-drawings").json()["items"]
    assert {item["id"] for item in drawings} == {drawing_a["id"], drawing_c["id"]}
    assert client.get(f"/part-drawings/{drawing_a['id']}").status_code == 200
    assert client.get(f"/part-drawings/{drawing_c['id']}").status_code == 200
    tasks = client.get("/quote-tasks").json()["items"]
    assert {item["id"] for item in tasks} == {task_a.json()["id"], task_c.json()["id"]}
    records = client.get("/admin/processing-records")
    assert records.status_code == 200
    names = {item["original_filename"] for item in records.json()["items"]}
    assert names == {"甲报价员-轴.pdf", "丙报价员-套.pdf"}
    uploaders = {item["uploaded_by_username"] for item in records.json()["items"]}
    assert uploaders == {"quoter_a", "quoter_c"}


def test_管理员能创建并停用本厂报价员账号(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_admin(db_session, factory_id, "admin_a", "secret-admin")
    db_session.commit()

    assert login(client, "admin_a", "secret-admin").status_code == 200
    created = client.post(
        "/admin/accounts",
        json={"username": "quoter_new", "password": "secret-new"},
    )
    assert created.status_code == 200
    assert created.json()["username"] == "quoter_new"
    assert created.json()["role"] == "quoter"
    assert created.json()["disabled_at"] is None

    listed = client.get("/admin/accounts")
    assert listed.status_code == 200
    usernames = {item["username"] for item in listed.json()["items"]}
    assert usernames == {"admin_a", "quoter_new"}

    _switch(client, "quoter_new", "secret-new")
    assert client.get("/auth/me").json()["username"] == "quoter_new"

    _switch(client, "admin_a", "secret-admin")
    disabled = client.post(f"/admin/accounts/{created.json()['id']}/disable")
    assert disabled.status_code == 200
    assert disabled.json()["disabled_at"] is not None

    client.post("/auth/logout")
    blocked = login(client, "quoter_new", "secret-new")
    assert blocked.status_code == 401
    assert "停用" in blocked.json()["detail"]


def test_报价员不能管理账号也不能读到其他厂数据(client: TestClient, db_session: Session) -> None:
    factory_a = create_factory(db_session, "华东精密")
    factory_b = create_factory(db_session, "南方模具")
    create_quoter(db_session, factory_a, "quoter_a", "secret-a")
    create_admin(db_session, factory_a, "admin_a", "secret-admin")
    create_admin(db_session, factory_b, "admin_b", "secret-b")
    db_session.commit()

    assert login(client, "quoter_a", "secret-a").status_code == 200
    assert client.get("/admin/accounts").status_code == 403
    assert client.post(
        "/admin/accounts", json={"username": "intruder", "password": "secret-xx"}
    ).status_code == 403
    assert client.get("/admin/processing-records").status_code == 403
    assert client.get("/admin/risk-rules").status_code == 403
    assert client.put("/admin/common-materials", json={"materials": ["45#"]}).status_code == 403

    _switch(client, "admin_a", "secret-admin")
    created = client.post(
        "/admin/accounts",
        json={"username": "factory_a_quoter", "password": "secret-new"},
    )
    assert created.status_code == 200

    _switch(client, "admin_b", "secret-b")
    listed = client.get("/admin/accounts")
    assert {item["username"] for item in listed.json()["items"]} == {"admin_b"}
    assert client.post(
        f"/admin/accounts/{created.json()['id']}/disable"
    ).status_code == 404
    records = client.get("/admin/processing-records")
    assert records.status_code == 200
    assert records.json() == {"items": []}


def test_管理员能配置常用材料并调整风险标签展示优先级(
    client: TestClient, db_session: Session
) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    create_admin(db_session, factory_id, "admin_a", "secret-admin")
    db_session.commit()

    assert login(client, "admin_a", "secret-admin").status_code == 200
    materials = client.put(
        "/admin/common-materials",
        json={"materials": ["45#", "40Cr", "6061"]},
    )
    assert materials.status_code == 200
    assert materials.json()["common_materials"] == ["45#", "40Cr", "6061"]

    priority = client.put(
        "/admin/risk-label-priority",
        json={"priority": ["细长", "薄壁", "深孔", "高精度"]},
    )
    assert priority.status_code == 200
    assert priority.json()["risk_label_priority"] == ["细长", "薄壁", "深孔", "高精度"]

    rules = client.get("/admin/risk-rules")
    assert rules.status_code == 200
    items = rules.json()["items"]
    assert {item["label_name"] for item in items} == {"高精度", "深孔", "薄壁", "细长"}
    assert all(item["provisional"] is True for item in items)
    assert all("threshold" in item and item["threshold"] for item in items)

    _switch(client, "quoter_a", "secret-a")
    prefs = client.get("/factory-preferences")
    assert prefs.status_code == 200
    assert prefs.json()["common_materials"] == ["45#", "40Cr", "6061"]
    assert prefs.json()["risk_label_priority"] == ["细长", "薄壁", "深孔", "高精度"]

    drawing = _upload(client, "WIRE-RL-01.png")
    extracted = client.post(f"/part-drawings/{drawing['id']}/extract")
    assert extracted.status_code == 200
    names = [label["name"] for label in extracted.json()["risk_labels"]]
    assert names == ["细长", "薄壁", "深孔", "高精度"]


def test_管理员界面没有报价底稿字段映射入口(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_admin(db_session, factory_id, "admin_a", "secret-admin")
    db_session.commit()

    assert login(client, "admin_a", "secret-admin").status_code == 200
    assert client.get("/admin/quote-sheet-template").status_code == 404
    assert client.get("/admin/field-mapping").status_code == 404
    prefs = client.get("/factory-preferences").json()
    assert "columns" not in prefs
    assert "source_key" not in prefs
    assert "mapping" not in prefs
