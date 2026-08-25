from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_admin, create_factory, create_quoter, insert_event, insert_part_drawing, login
from quote_assistant.domain.entities import PartDrawingStatus

HIGH_RISK_KEYS = ("tightest_tolerance", "max_envelope", "deepest_hole", "thinnest_wall")


def _upload(client: TestClient, filename: str) -> dict:
    response = client.post(
        "/part-drawings",
        files=[("files", (filename, PNG_1X1, "image/png"))],
    )
    assert response.status_code == 200
    return response.json()["items"][0]


def _complete_review_flow(client: TestClient, drawing_id: str) -> None:
    for key in HIGH_RISK_KEYS:
        confirmed = client.post(f"/part-drawings/{drawing_id}/fields/{key}/confirm")
        assert confirmed.status_code == 200
    done = client.post(f"/part-drawings/{drawing_id}/complete-review")
    assert done.status_code == 200
    assert done.json()["status"] == "已复核"


def test_走完全流程后上传与已复核时间戳都在且处理耗时可算出(
    client: TestClient, db_session: Session
) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    create_admin(db_session, factory_id, "admin_a", "secret-admin")
    db_session.commit()

    assert login(client, "quoter_a", "secret-a").status_code == 200
    item = _upload(client, "FX-TQ-01.png")
    drawing_id = item["id"]
    _complete_review_flow(client, drawing_id)

    events = client.get(f"/part-drawings/{drawing_id}/events").json()["items"]
    uploaded = next(row for row in events if row["to_status"] == "已上传")
    reviewed = next(row for row in events if row["to_status"] == "已复核")
    assert uploaded["occurred_at"]
    assert reviewed["occurred_at"]

    client.post("/auth/logout")
    assert login(client, "admin_a", "secret-admin").status_code == 200
    comparison = client.get("/processing-time")
    assert comparison.status_code == 200
    body = comparison.json()
    assert body["reviewed_count"] == 1
    assert body["excluded_unreviewed_count"] == 0
    assert len(body["items"]) == 1
    computed = body["items"][0]
    assert computed["part_drawing_id"] == drawing_id
    assert computed["uploaded_at"] == uploaded["occurred_at"]
    assert computed["reviewed_at"] == reviewed["occurred_at"]
    expected = (
        datetime.fromisoformat(reviewed["occurred_at"]) - datetime.fromisoformat(uploaded["occurred_at"])
    ).total_seconds()
    assert computed["processing_seconds"] == expected
    assert computed["grading_seconds"] is not None
    assert computed["extraction_seconds"] is not None
    assert computed["review_seconds"] is not None
    assert computed["processing_seconds"] == pytest.approx(
        computed["grading_seconds"] + computed["extraction_seconds"] + computed["review_seconds"]
    )


def test_未复核零件图不计入处理耗时避免半成品拉低数据(
    client: TestClient, db_session: Session
) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_admin(db_session, factory_id, "admin_a", "secret-admin")
    uploaded_at = datetime(2026, 8, 1, 8, 0, tzinfo=UTC)
    reviewed = insert_part_drawing(
        db_session, factory_id, "已复核轴套.png", status=PartDrawingStatus.REVIEWED
    )
    unfinished = insert_part_drawing(
        db_session, factory_id, "未复核法兰.png", status=PartDrawingStatus.EXTRACTED
    )
    insert_event(
        db_session,
        drawing_id=reviewed,
        factory_id=factory_id,
        to_status=PartDrawingStatus.UPLOADED,
        occurred_at=uploaded_at,
        sequence_no=1,
    )
    insert_event(
        db_session,
        drawing_id=reviewed,
        factory_id=factory_id,
        from_status=PartDrawingStatus.UPLOADED,
        to_status=PartDrawingStatus.GRADED,
        occurred_at=uploaded_at + timedelta(minutes=2),
        sequence_no=2,
    )
    insert_event(
        db_session,
        drawing_id=reviewed,
        factory_id=factory_id,
        from_status=PartDrawingStatus.GRADED,
        to_status=PartDrawingStatus.EXTRACTED,
        occurred_at=uploaded_at + timedelta(minutes=5),
        sequence_no=3,
    )
    insert_event(
        db_session,
        drawing_id=reviewed,
        factory_id=factory_id,
        from_status=PartDrawingStatus.EXTRACTED,
        to_status=PartDrawingStatus.REVIEWED,
        occurred_at=uploaded_at + timedelta(minutes=10),
        sequence_no=4,
    )
    insert_event(
        db_session,
        drawing_id=unfinished,
        factory_id=factory_id,
        to_status=PartDrawingStatus.UPLOADED,
        occurred_at=uploaded_at,
        sequence_no=1,
    )
    db_session.commit()

    assert login(client, "admin_a", "secret-admin").status_code == 200
    body = client.get("/processing-time").json()
    assert body["reviewed_count"] == 1
    assert body["excluded_unreviewed_count"] == 1
    assert [row["part_drawing_id"] for row in body["items"]] == [str(reviewed)]
    assert body["items"][0]["processing_seconds"] == 600
    assert body["items"][0]["grading_seconds"] == 120
    assert body["items"][0]["extraction_seconds"] == 180
    assert body["items"][0]["review_seconds"] == 300
    assert body["average_processing_seconds"] == 600
    assert body["average_grading_seconds"] == 120
    assert body["average_extraction_seconds"] == 180
    assert body["average_review_seconds"] == 300


def test_管理员能录入人工基线并看到本厂对比(
    client: TestClient, db_session: Session
) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_admin(db_session, factory_id, "admin_a", "secret-admin")
    uploaded_at = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)
    drawing_id = insert_part_drawing(
        db_session, factory_id, "已复核套筒.png", status=PartDrawingStatus.REVIEWED
    )
    insert_event(
        db_session,
        drawing_id=drawing_id,
        factory_id=factory_id,
        to_status=PartDrawingStatus.UPLOADED,
        occurred_at=uploaded_at,
        sequence_no=1,
    )
    insert_event(
        db_session,
        drawing_id=drawing_id,
        factory_id=factory_id,
        from_status=PartDrawingStatus.UPLOADED,
        to_status=PartDrawingStatus.REVIEWED,
        occurred_at=uploaded_at + timedelta(minutes=8),
        sequence_no=2,
    )
    db_session.commit()

    assert login(client, "admin_a", "secret-admin").status_code == 200
    created = client.post(
        "/manual-baselines",
        json={"part_description": "φ40 回转轴，纯人工抄写", "manual_duration_seconds": 1200},
    )
    assert created.status_code == 200
    baseline = created.json()
    assert baseline["part_description"] == "φ40 回转轴，纯人工抄写"
    assert baseline["manual_duration_seconds"] == 1200
    assert baseline["recorded_at"]

    body = client.get("/processing-time").json()
    assert body["baseline_count"] == 1
    assert body["average_baseline_seconds"] == 1200
    assert body["average_processing_seconds"] == 480
    assert body["saved_seconds"] == 720
    assert body["baselines"][0]["part_description"] == "φ40 回转轴，纯人工抄写"


def test_报价员不能查看处理耗时也不能录入人工基线(
    client: TestClient, db_session: Session
) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()

    assert login(client, "quoter_a", "secret-a").status_code == 200
    assert client.get("/processing-time").status_code == 403
    blocked = client.post(
        "/manual-baselines",
        json={"part_description": "不该录入", "manual_duration_seconds": 600},
    )
    assert blocked.status_code == 403
    assert "管理员" in blocked.json()["detail"]


def test_甲厂管理员看不到乙厂处理耗时与人工基线(
    client: TestClient, db_session: Session
) -> None:
    factory_a = create_factory(db_session, "华东精密")
    factory_b = create_factory(db_session, "南方模具")
    create_admin(db_session, factory_a, "admin_a", "secret-a")
    create_admin(db_session, factory_b, "admin_b", "secret-b")
    uploaded_at = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
    drawing_b = insert_part_drawing(
        db_session, factory_b, "乙厂已复核.png", status=PartDrawingStatus.REVIEWED
    )
    insert_event(
        db_session,
        drawing_id=drawing_b,
        factory_id=factory_b,
        to_status=PartDrawingStatus.UPLOADED,
        occurred_at=uploaded_at,
        sequence_no=1,
    )
    insert_event(
        db_session,
        drawing_id=drawing_b,
        factory_id=factory_b,
        from_status=PartDrawingStatus.UPLOADED,
        to_status=PartDrawingStatus.REVIEWED,
        occurred_at=uploaded_at + timedelta(minutes=15),
        sequence_no=2,
    )
    db_session.commit()

    assert login(client, "admin_b", "secret-b").status_code == 200
    created = client.post(
        "/manual-baselines",
        json={"part_description": "乙厂纯人工法兰", "manual_duration_seconds": 1800},
    )
    assert created.status_code == 200
    as_b = client.get("/processing-time").json()
    assert as_b["reviewed_count"] == 1
    assert as_b["baseline_count"] == 1
    assert as_b["items"][0]["original_filename"] == "乙厂已复核.png"

    client.post("/auth/logout")
    assert login(client, "admin_a", "secret-a").status_code == 200
    as_a = client.get("/processing-time")
    assert as_a.status_code == 200
    empty = as_a.json()
    assert empty["reviewed_count"] == 0
    assert empty["excluded_unreviewed_count"] == 0
    assert empty["baseline_count"] == 0
    assert empty["items"] == []
    assert empty["baselines"] == []
    assert empty["average_processing_seconds"] is None
    assert empty["average_baseline_seconds"] is None
    assert empty["saved_seconds"] is None


def test_处理耗时与基线忽略调用方传入的工厂标识(
    client: TestClient, db_session: Session
) -> None:
    factory_a = create_factory(db_session, "华东精密")
    factory_b = create_factory(db_session, "南方模具")
    create_admin(db_session, factory_a, "admin_a", "secret-a")
    db_session.commit()

    assert login(client, "admin_a", "secret-a").status_code == 200
    created = client.post(
        "/manual-baselines",
        json={
            "part_description": "甲厂基线",
            "manual_duration_seconds": 900,
            "factory_id": str(factory_b),
            "tenant_id": str(factory_b),
        },
    )
    assert created.status_code == 200
    leaked = client.get(
        "/processing-time",
        params={"factory_id": str(factory_b), "tenant_id": str(factory_b)},
    )
    assert leaked.status_code == 200
    body = leaked.json()
    assert body["baseline_count"] == 1
    assert body["baselines"][0]["part_description"] == "甲厂基线"
    assert body["reviewed_count"] == 0
