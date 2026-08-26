from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, insert_quote_task, login
from quote_assistant.adapter.db.models import QuoteTaskRow
from quote_assistant.domain.quote_task import QuoteTask
from quote_assistant.interface.http.schemas import (
    CreateQuoteTaskRequest,
    QuoteTaskDetailResponse,
    QuoteTaskSummaryResponse,
)


HIGH_RISK_KEYS = ("tightest_tolerance", "max_envelope", "deepest_hole", "thinnest_wall")


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


def _create_task(client: TestClient, name: str, customer_name: str) -> dict:
    response = client.post(
        "/quote-tasks",
        json={"name": name, "customer_name": customer_name},
    )
    assert response.status_code == 200
    return response.json()


def _complete_review(client: TestClient, drawing_id: str) -> None:
    for key in HIGH_RISK_KEYS:
        confirmed = client.post(f"/part-drawings/{drawing_id}/fields/{key}/confirm")
        assert confirmed.status_code == 200
    done = client.post(f"/part-drawings/{drawing_id}/complete-review")
    assert done.status_code == 200
    assert done.json()["status"] == "已复核"


def test_新上传的零件图不属于任何报价任务(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    drawing = _upload(client, "FX-TQ-01.png")
    assert drawing["quote_task_id"] is None
    assert client.get("/quote-tasks").json() == {"items": []}


def test_报价员能创建报价任务并填写名称与客户(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    created = _create_task(client, "南方汽配八月询价", "南方汽配")

    assert created["name"] == "南方汽配八月询价"
    assert created["customer_name"] == "南方汽配"
    assert created["review_status"] == "无零件图"
    assert created["unreviewed_member_count"] == 0
    assert created["drawings"] == []
    assert "amount" not in created
    assert "price" not in created
    assert "approval" not in created
    assert "审批" not in created

    listed = client.get("/quote-tasks")
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1
    assert listed.json()["items"][0]["customer_name"] == "南方汽配"


def test_空名称或客户名称被拒绝(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    blank_name = client.post("/quote-tasks", json={"name": "   ", "customer_name": "南方汽配"})
    assert blank_name.status_code == 400
    assert "任务名称" in blank_name.json()["detail"]

    blank_customer = client.post("/quote-tasks", json={"name": "八月询价", "customer_name": "  "})
    assert blank_customer.status_code == 400
    assert "客户名称" in blank_customer.json()["detail"]


def test_能把零件图归入移出或移到另一个报价任务(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    first = _upload(client, "FX-TQ-01.png")
    second = _upload(client, "FX-TA-01.png")
    task_a = _create_task(client, "任务甲", "客户甲")
    task_b = _create_task(client, "任务乙", "客户乙")

    assigned = client.post(
        f"/quote-tasks/{task_a['id']}/part-drawings",
        json={"part_drawing_id": first["id"]},
    )
    assert assigned.status_code == 200
    assert len(assigned.json()["drawings"]) == 1
    assert assigned.json()["drawings"][0]["id"] == first["id"]
    assert assigned.json()["review_status"] == "复核未完成"

    drawing = client.get(f"/part-drawings/{first['id']}").json()
    assert drawing["quote_task_id"] == task_a["id"]
    ungrouped = client.get(f"/part-drawings/{second['id']}").json()
    assert ungrouped["quote_task_id"] is None

    moved = client.post(
        f"/quote-tasks/{task_b['id']}/part-drawings",
        json={"part_drawing_id": first["id"]},
    )
    assert moved.status_code == 200
    assert [row["id"] for row in moved.json()["drawings"]] == [first["id"]]
    leftover = client.get(f"/quote-tasks/{task_a['id']}")
    assert leftover.json()["drawings"] == []
    assert leftover.json()["review_status"] == "无零件图"
    assert client.get(f"/part-drawings/{first['id']}").json()["quote_task_id"] == task_b["id"]

    removed = client.delete(f"/quote-tasks/{task_b['id']}/part-drawings/{first['id']}")
    assert removed.status_code == 200
    assert removed.json()["drawings"] == []
    assert client.get(f"/part-drawings/{first['id']}").json()["quote_task_id"] is None
    assert client.get(f"/part-drawings/{second['id']}").json()["quote_task_id"] is None


def test_一张零件图同时最多属于一个报价任务(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    drawing = _upload(client, "FX-TQ-01.png")
    task_a = _create_task(client, "任务甲", "客户甲")
    task_b = _create_task(client, "任务乙", "客户乙")

    client.post(
        f"/quote-tasks/{task_a['id']}/part-drawings",
        json={"part_drawing_id": drawing["id"]},
    )
    client.post(
        f"/quote-tasks/{task_b['id']}/part-drawings",
        json={"part_drawing_id": drawing["id"]},
    )

    listed = client.get("/part-drawings").json()["items"]
    matches = [item for item in listed if item["id"] == drawing["id"]]
    assert len(matches) == 1
    assert matches[0]["quote_task_id"] == task_b["id"]
    assert len(client.get(f"/quote-tasks/{task_a['id']}").json()["drawings"]) == 0
    assert len(client.get(f"/quote-tasks/{task_b['id']}").json()["drawings"]) == 1


def test_历史记录可按客户时间与复核状态检索(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200

    older = _create_task(client, "三月询价", "南方汽配")
    newer = _create_task(client, "八月询价", "东海法兰")
    empty = _create_task(client, "空任务", "南方汽配")

    row = db_session.get(QuoteTaskRow, UUID(older["id"]))
    assert row is not None
    row.created_at = datetime.now(UTC) - timedelta(days=10)
    db_session.commit()

    drawing = _upload(client, "FX-TQ-01.png")
    client.post(
        f"/quote-tasks/{older['id']}/part-drawings",
        json={"part_drawing_id": drawing["id"]},
    )
    _complete_review(client, drawing["id"])
    unfinished_drawing = _upload(client, "FX-TA-01.png")
    client.post(
        f"/quote-tasks/{newer['id']}/part-drawings",
        json={"part_drawing_id": unfinished_drawing["id"]},
    )

    by_customer = client.get("/quote-tasks", params={"customer_name": "南方"})
    assert {item["id"] for item in by_customer.json()["items"]} == {older["id"], empty["id"]}

    by_reviewed = client.get("/quote-tasks", params={"review_status": "已复核"})
    assert [item["id"] for item in by_reviewed.json()["items"]] == [older["id"]]
    assert by_reviewed.json()["items"][0]["review_status"] == "已复核"

    by_incomplete = client.get("/quote-tasks", params={"review_status": "复核未完成"})
    assert [item["id"] for item in by_incomplete.json()["items"]] == [newer["id"]]

    by_empty = client.get("/quote-tasks", params={"review_status": "无零件图"})
    assert [item["id"] for item in by_empty.json()["items"]] == [empty["id"]]

    cutoff = (datetime.now(UTC) - timedelta(days=5)).date().isoformat()
    recent = client.get("/quote-tasks", params={"created_from": cutoff})
    assert {item["id"] for item in recent.json()["items"]} == {newer["id"], empty["id"]}

    older_only = client.get("/quote-tasks", params={"created_to": cutoff})
    assert [item["id"] for item in older_only.json()["items"]] == [older["id"]]


def test_详情列出零件图及各自复核状态(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    reviewed = _upload(client, "FX-TQ-01.png")
    pending = _upload(client, "FX-TA-01.png")
    task = _create_task(client, "混装询价", "东海法兰")
    client.post(
        f"/quote-tasks/{task['id']}/part-drawings",
        json={"part_drawing_id": reviewed["id"]},
    )
    client.post(
        f"/quote-tasks/{task['id']}/part-drawings",
        json={"part_drawing_id": pending["id"]},
    )
    _complete_review(client, reviewed["id"])

    detail = client.get(f"/quote-tasks/{task['id']}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["review_status"] == "复核未完成"
    assert body["unreviewed_member_count"] == 1
    statuses = {row["id"]: row["status"] for row in body["drawings"]}
    assert statuses[reviewed["id"]] == "已复核"
    assert statuses[pending["id"]] == "已提取"
    assert "amount" not in body
    assert "approval" not in body


def test_报价任务模型没有金额和审批字段() -> None:
    assert set(QuoteTask.__dataclass_fields__) == {
        "id",
        "factory_id",
        "name",
        "customer_name",
        "created_at",
        "created_by_user_id",
    }
    assert set(CreateQuoteTaskRequest.model_fields) == {"name", "customer_name"}
    assert "amount" not in QuoteTaskSummaryResponse.model_fields
    assert "price" not in QuoteTaskSummaryResponse.model_fields
    assert "approval" not in QuoteTaskSummaryResponse.model_fields
    assert "amount" not in QuoteTaskDetailResponse.model_fields
    assert "approval" not in QuoteTaskDetailResponse.model_fields
    assert "unreviewed_member_count" in QuoteTaskDetailResponse.model_fields


def test_插入辅助可指定创建时间(db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    user_id = create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    when = datetime(2026, 3, 1, tzinfo=UTC)
    task_id = insert_quote_task(
        db_session,
        factory_id,
        "三月询价",
        "南方汽配",
        user_id,
        created_at=when,
    )
    db_session.commit()
    row = db_session.get(QuoteTaskRow, task_id)
    assert row is not None
    assert row.created_at == when
