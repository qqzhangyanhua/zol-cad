from __future__ import annotations

import inspect
import json
import zipfile
from io import BytesIO
from urllib.parse import unquote

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_admin, create_factory, create_quoter, login
from quote_assistant.domain.tenant_data import tenant_delete_confirm_phrase
from quote_assistant.usecase.delete_tenant_data import DeleteTenantData
from quote_assistant.usecase.export_tenant_data import ExportTenantData
from quote_assistant.usecase.request_tenant_delete import RequestTenantDelete

HIGH_RISK_KEYS = ("tightest_tolerance", "max_envelope", "deepest_hole", "thinnest_wall")


def _upload(client: TestClient, filename: str) -> dict:
    response = client.post(
        "/part-drawings",
        files=[("files", (filename, PNG_1X1, "image/png"))],
    )
    assert response.status_code == 200
    return response.json()["items"][0]


def _complete_review(client: TestClient, drawing_id: str) -> dict:
    detail = client.get(f"/part-drawings/{drawing_id}")
    assert detail.status_code == 200
    for field in detail.json()["extracted_fields"]:
        if field["requires_confirmation"] and not field["confirmed"] and not field["ignored"]:
            confirmed = client.post(f"/part-drawings/{drawing_id}/fields/{field['key']}/confirm")
            assert confirmed.status_code == 200
    done = client.post(f"/part-drawings/{drawing_id}/complete-review")
    assert done.status_code == 200
    return done.json()


def _open_zip(content: bytes) -> zipfile.ZipFile:
    return zipfile.ZipFile(BytesIO(content))


def test_导出与删除用例不接受工厂标识参数() -> None:
    for cls in (ExportTenantData, RequestTenantDelete, DeleteTenantData):
        names = list(inspect.signature(cls.execute).parameters)
        assert "factory_id" not in names
        assert "tenant_id" not in names


def test_报价员不能导出或删除本厂数据(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200

    exported = client.get("/admin/tenant-data/export", params={"factory_id": str(factory_id)})
    assert exported.status_code == 403
    challenge = client.post(
        "/admin/tenant-data/delete-challenge", json={"factory_id": str(factory_id)}
    )
    assert challenge.status_code == 403
    deleted = client.post(
        "/admin/tenant-data/delete",
        json={"confirm_token": "x", "confirm_phrase": "删除华东精密的全部数据"},
    )
    assert deleted.status_code == 403


def test_管理员能导出可读压缩包且删除需服务端二次确认_删除甲厂不影响乙厂(
    client: TestClient, db_session: Session, app
) -> None:
    factory_a = create_factory(db_session, "华东精密")
    factory_b = create_factory(db_session, "南方模具")
    create_quoter(db_session, factory_a, "quoter_a", "secret-a")
    create_admin(db_session, factory_a, "admin_a", "secret-admin-a")
    create_quoter(db_session, factory_b, "quoter_b", "secret-b")
    create_admin(db_session, factory_b, "admin_b", "secret-admin-b")
    db_session.commit()

    assert login(client, "quoter_a", "secret-a").status_code == 200
    drawing_a = _upload(client, "WIRE-RL-01-FX-TQ.png")
    patched = client.patch(
        f"/part-drawings/{drawing_a['id']}/fields/drawing_no",
        json={"value": "A-1001"},
    )
    assert patched.status_code == 200
    _complete_review(client, drawing_a["id"])
    task_a = client.post("/quote-tasks", json={"name": "甲厂询价", "customer_name": "甲厂客户"})
    assert task_a.status_code == 200
    assigned = client.post(
        f"/quote-tasks/{task_a.json()['id']}/part-drawings",
        json={"part_drawing_id": drawing_a["id"]},
    )
    assert assigned.status_code == 200
    storage_key_a = f"part-drawings/{factory_a}/{drawing_a['id']}/original.png"
    assert app.state.object_storage.fetch(storage_key_a)

    client.post("/auth/logout")
    assert login(client, "quoter_b", "secret-b").status_code == 200
    drawing_b = _upload(client, "乙厂-法兰.png")
    task_b = client.post("/quote-tasks", json={"name": "乙厂询价", "customer_name": "乙厂客户"})
    assert task_b.status_code == 200
    assigned_b = client.post(
        f"/quote-tasks/{task_b.json()['id']}/part-drawings",
        json={"part_drawing_id": drawing_b["id"]},
    )
    assert assigned_b.status_code == 200
    storage_key_b = f"part-drawings/{factory_b}/{drawing_b['id']}/original.png"
    assert app.state.object_storage.fetch(storage_key_b)

    client.post("/auth/logout")
    assert login(client, "admin_a", "secret-admin-a").status_code == 200
    exported = client.get("/admin/tenant-data/export", params={"factory_id": str(factory_b)})
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("application/zip")
    assert "本厂数据导出" in unquote(exported.headers["content-disposition"])

    with _open_zip(exported.content) as archive:
        names = set(archive.namelist())
        assert "README.md" in names
        assert "manifest.json" in names
        assert "part_drawings.json" in names
        assert "part_drawings.csv" in names
        assert "quote_tasks.json" in names
        assert "quote_tasks.csv" in names
        assert "correction_records.json" in names
        assert "correction_records.csv" in names
        readme = archive.read("README.md").decode("utf-8")
        assert "零件图" in readme
        assert "JSON" in readme
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["factory_name"] == "华东精密"
        assert manifest["counts"]["part_drawings"] == 1
        drawings = json.loads(archive.read("part_drawings.json"))
        assert len(drawings) == 1
        exported_drawing = drawings[0]
        assert exported_drawing["id"] == drawing_a["id"]
        assert exported_drawing["original_filename"] == "WIRE-RL-01-FX-TQ.png"
        assert any(
            field["key"] == "drawing_no" and field["value"] == "A-1001"
            for field in exported_drawing["extracted_fields"]
        )
        assert exported_drawing["review"]["status"] == "已复核"
        assert exported_drawing["risk_labels"]
        assert {label["name"] for label in exported_drawing["risk_labels"]}
        original_path = exported_drawing["original_archive_path"]
        assert original_path in names
        assert archive.read(original_path) == PNG_1X1
        tasks = json.loads(archive.read("quote_tasks.json"))
        assert len(tasks) == 1
        assert tasks[0]["name"] == "甲厂询价"
        assert drawing_a["id"] in tasks[0]["part_drawing_ids"]
        corrections = json.loads(archive.read("correction_records.json"))
        assert len(corrections) == 1
        assert corrections[0]["old_value"] != "A-1001"
        assert corrections[0]["new_value"] == "A-1001"
        csv_text = archive.read("part_drawings.csv").decode("utf-8-sig")
        assert "A-1001" in csv_text
        assert "乙厂-法兰.png" not in archive.read("part_drawings.json").decode("utf-8")
        assert "乙厂询价" not in archive.read("quote_tasks.json").decode("utf-8")

    rejected = client.post(
        "/admin/tenant-data/delete",
        json={
            "confirm_token": "not-a-real-token",
            "confirm_phrase": tenant_delete_confirm_phrase("华东精密"),
        },
    )
    assert rejected.status_code == 400
    assert client.get("/part-drawings").json()["items"]

    challenge = client.post("/admin/tenant-data/delete-challenge")
    assert challenge.status_code == 200
    body = challenge.json()
    assert body["confirm_phrase"] == "删除华东精密的全部数据"
    assert body["confirm_token"]

    wrong_phrase = client.post(
        "/admin/tenant-data/delete",
        json={"confirm_token": body["confirm_token"], "confirm_phrase": "确认删除"},
    )
    assert wrong_phrase.status_code == 400
    assert len(client.get("/part-drawings").json()["items"]) == 1

    deleted = client.post(
        "/admin/tenant-data/delete",
        json={
            "confirm_token": body["confirm_token"],
            "confirm_phrase": body["confirm_phrase"],
            "factory_id": str(factory_b),
        },
    )
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    reused = client.post(
        "/admin/tenant-data/delete",
        json={"confirm_token": body["confirm_token"], "confirm_phrase": body["confirm_phrase"]},
    )
    assert reused.status_code == 400

    assert client.get("/part-drawings").json() == {"items": []}
    assert client.get("/quote-tasks").json() == {"items": []}
    assert client.get("/correction-stats").json()["items"] == []
    assert client.get("/admin/processing-records").json() == {"items": []}
    accounts = client.get("/admin/accounts").json()["items"]
    assert {row["username"] for row in accounts} >= {"admin_a", "quoter_a"}

    try:
        app.state.object_storage.fetch(storage_key_a)
        raise AssertionError("甲厂原图仍留在对象存储")
    except FileNotFoundError:
        pass

    client.post("/auth/logout")
    assert login(client, "quoter_a", "secret-a").status_code == 200
    assert client.get("/part-drawings").json() == {"items": []}
    assert client.get("/quote-tasks").json() == {"items": []}

    client.post("/auth/logout")
    assert login(client, "admin_b", "secret-admin-b").status_code == 200
    leftover = client.get("/part-drawings").json()["items"]
    assert len(leftover) == 1
    assert leftover[0]["id"] == drawing_b["id"]
    assert leftover[0]["original_filename"] == "乙厂-法兰.png"
    tasks = client.get("/quote-tasks").json()["items"]
    assert len(tasks) == 1
    assert tasks[0]["name"] == "乙厂询价"
    assert app.state.object_storage.fetch(storage_key_b) == PNG_1X1
    original = client.get(f"/part-drawings/{drawing_b['id']}/original")
    assert original.status_code == 200
