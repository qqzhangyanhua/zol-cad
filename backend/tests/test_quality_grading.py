from __future__ import annotations

import inspect
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, login
from quote_assistant.domain.quality import (
    ASSEMBLY_OUT_OF_SCOPE_TEXT,
    LOW_QUALITY_MARK_TEXT,
    POOR_GRADE_ADVISE_TEXT,
    QUALITY_GRADE_DISCLAIMER,
)
from quote_assistant.usecase.continue_despite_poor_quality import ContinueDespitePoorQuality
from quote_assistant.usecase.extract_part_drawing import ExtractPartDrawing
from quote_assistant.usecase.list_part_drawing_events import ListPartDrawingEvents
from quote_assistant.usecase.upload_part_drawings import UploadPartDrawings


def _upload(client: TestClient, filename: str):
    return client.post(
        "/part-drawings",
        files=[("files", (filename, PNG_1X1, "image/png"))],
    )


def _login_quoter(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200


def test_分级用例不接受工厂标识参数() -> None:
    for cls in (
        UploadPartDrawings,
        ContinueDespitePoorQuality,
        ExtractPartDrawing,
        ListPartDrawingEvents,
    ):
        names = list(inspect.signature(cls.execute).parameters)
        assert "factory_id" not in names
        assert "tenant_id" not in names


def test_上传后零件图自动分级为清晰或一般或差(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)

    clear = _upload(client, "FX-TQ-01.png").json()["items"][0]
    average = _upload(client, "FX-TA-01.png").json()["items"][0]
    poor = _upload(client, "FX-TP-01.png").json()["items"][0]

    assert clear["quality_grade"] == "清晰"
    assert clear["status"] == "已提取"
    assert clear["auto_prefill_allowed"] is True
    assert clear["quality_grade_disclaimer"] == QUALITY_GRADE_DISCLAIMER

    assert average["quality_grade"] == "一般"
    assert average["status"] == "已提取"
    assert average["auto_prefill_allowed"] is True

    assert poor["quality_grade"] == "差"
    assert poor["status"] == "建议人工"
    assert poor["auto_prefill_allowed"] is False


def test_差图不自动预填并建议走人工(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    uploaded = _upload(client, "FX-TP-01.png")
    assert uploaded.status_code == 200
    item = uploaded.json()["items"][0]

    assert item["quality_grade"] == "差"
    assert item["status"] == "建议人工"
    assert item["auto_prefill_allowed"] is False
    assert item["low_quality_unreliable"] is False
    assert item["advise_manual_message"] == POOR_GRADE_ADVISE_TEXT
    assert "自动预填" in item["advise_manual_message"]
    assert "建议走人工" in item["advise_manual_message"]

    listed = client.get("/part-drawings").json()["items"][0]
    assert listed["id"] == item["id"]
    assert listed["auto_prefill_allowed"] is False
    assert listed["status"] == "建议人工"


def test_显式仍然继续后结果永久携带低质量标记(
    client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    drawing_id = _upload(client, "FX-TP-01.png").json()["items"][0]["id"]

    continued = client.post(f"/part-drawings/{drawing_id}/continue-despite-quality")
    assert continued.status_code == 200
    body = continued.json()
    assert body["status"] == "已提取"
    assert body["quality_grade"] == "差"
    assert body["low_quality_unreliable"] is True
    assert body["low_quality_mark"] == LOW_QUALITY_MARK_TEXT
    assert body["auto_prefill_allowed"] is True
    assert body["advise_manual_message"] is None

    detail = client.get(f"/part-drawings/{drawing_id}").json()
    assert detail["low_quality_unreliable"] is True
    assert detail["low_quality_mark"] == LOW_QUALITY_MARK_TEXT

    listed = client.get("/part-drawings").json()["items"][0]
    assert listed["id"] == drawing_id
    assert listed["low_quality_unreliable"] is True
    assert listed["low_quality_mark"] == LOW_QUALITY_MARK_TEXT


def test_清晰图不能走仍然继续(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    drawing_id = _upload(client, "FX-TQ-01.png").json()["items"][0]["id"]
    response = client.post(f"/part-drawings/{drawing_id}/continue-despite-quality")
    assert response.status_code == 409
    assert client.get(f"/part-drawings/{drawing_id}").json()["low_quality_unreliable"] is False


def test_装配图被明确告知不在处理范围(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-ASM-01.png").json()["items"][0]
    assert item["is_assembly_or_exploded"] is True
    assert item["status"] == "不在范围"
    assert item["auto_prefill_allowed"] is False
    assert item["out_of_scope_message"] == ASSEMBLY_OUT_OF_SCOPE_TEXT
    blocked = client.post(f"/part-drawings/{item['id']}/continue-despite-quality")
    assert blocked.status_code == 409


def test_每次状态迁移都写入可按零件图查询的带时间戳事件(
    client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    drawing_id = _upload(client, "FX-TP-01.png").json()["items"][0]["id"]

    events = client.get(f"/part-drawings/{drawing_id}/events")
    assert events.status_code == 200
    items = events.json()["items"]
    assert [row["to_status"] for row in items] == ["已上传", "分级中", "建议人工"]
    assert [row["from_status"] for row in items] == [None, "已上传", "分级中"]
    assert [row["sequence_no"] for row in items] == [1, 2, 3]
    times = [datetime.fromisoformat(row["occurred_at"]) for row in items]
    assert times == sorted(times)

    client.post(f"/part-drawings/{drawing_id}/continue-despite-quality")
    after = client.get(f"/part-drawings/{drawing_id}/events").json()["items"]
    assert [row["to_status"] for row in after] == [
        "已上传",
        "分级中",
        "建议人工",
        "已分级",
        "提取中",
        "已提取",
    ]
    assert after[3]["from_status"] == "建议人工"
    assert after[3]["sequence_no"] == 4
    assert after[-1]["to_status"] == "已提取"
    assert after[-1]["sequence_no"] == 6


def test_假引擎按输入图标识返回预置分级(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    named = _upload(client, "客户询价-FX-TA-01-轴套.png").json()["items"][0]
    unknown = _upload(client, "随机零件.png").json()["items"][0]
    assert named["quality_grade"] == "一般"
    assert unknown["quality_grade"] == "清晰"
    assert unknown["status"] == "已提取"
