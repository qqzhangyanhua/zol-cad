from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, login
from quote_assistant.adapter.extraction.fake import FixtureExtractionEngine
from quote_assistant.domain.extraction import ExtractionRequest, ExtractionResult
from quote_assistant.domain.part_family import (
    EXPERIMENTAL_MARK_TEXT,
    PROVISIONAL_OTHER_PART_FAMILY_ID,
    TARGET_PART_FAMILY_ID,
    UNKNOWN_PART_FAMILY_ID,
    classify_part_family,
    experimental_mark_for,
)
from quote_assistant.domain.prompt_templates import prompt_template_for

HIGH_RISK_KEYS = ("tightest_tolerance", "max_envelope", "deepest_hole", "thinnest_wall")


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


class _RecordingEngine:
    def __init__(self) -> None:
        self.requests: list[ExtractionRequest] = []
        self.prompt_ids: list[str] = []
        self._inner = FixtureExtractionEngine()

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        self.requests.append(request)
        self.prompt_ids.append(prompt_template_for(request.part_family_id).id)
        return self._inner.extract(request)


def test_每张零件图记录所属族类(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    target = _upload(client, "FX-TQ-01.png").json()["items"][0]
    other = _upload(client, "FX-NQ-01.png").json()["items"][0]
    unknown = _upload(client, "随机零件.png").json()["items"][0]

    assert target["part_family_id"] == TARGET_PART_FAMILY_ID
    assert other["part_family_id"] == PROVISIONAL_OTHER_PART_FAMILY_ID
    assert unknown["part_family_id"] == UNKNOWN_PART_FAMILY_ID
    assert classify_part_family("FX-TA-01.png") == TARGET_PART_FAMILY_ID
    assert classify_part_family("FX-NA-01.png") == PROVISIONAL_OTHER_PART_FAMILY_ID


def test_目标族走该族专用提示词模板且族类作为Port参数(
    app, client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    engine = _RecordingEngine()
    app.state.extraction_engine = engine

    item = _upload(client, "FX-TQ-01.png").json()["items"][0]
    assert item["is_target_part_family"] is True
    assert item["experimental_mark"] is None
    assert engine.requests
    assert {request.part_family_id for request in engine.requests} == {TARGET_PART_FAMILY_ID}
    dedicated = prompt_template_for(TARGET_PART_FAMILY_ID)
    assert dedicated.id == "prompt.provisional-target-family"
    assert dedicated.family_id == TARGET_PART_FAMILY_ID
    assert set(engine.prompt_ids) == {dedicated.id}
    assert prompt_template_for(PROVISIONAL_OTHER_PART_FAMILY_ID).id != dedicated.id


def test_非目标族的零件图结果在详情与列表携带实验性标记(
    client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    uploaded = _upload(client, "FX-NQ-01.png")
    assert uploaded.status_code == 200
    item = uploaded.json()["items"][0]
    assert item["part_family_id"] == PROVISIONAL_OTHER_PART_FAMILY_ID
    assert item["is_target_part_family"] is False
    assert item["experimental_mark"] == EXPERIMENTAL_MARK_TEXT
    assert experimental_mark_for(item["part_family_id"]) == EXPERIMENTAL_MARK_TEXT

    detail = client.get(f"/part-drawings/{item['id']}").json()
    listed = next(
        row for row in client.get("/part-drawings").json()["items"] if row["id"] == item["id"]
    )
    assert detail["experimental_mark"] == EXPERIMENTAL_MARK_TEXT
    assert listed["experimental_mark"] == EXPERIMENTAL_MARK_TEXT
    assert detail["look_at_drawing_disclaimer"]
    assert listed["look_at_drawing_disclaimer"]


def test_未知族同样标注实验性不保证(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "随机零件.png").json()["items"][0]
    assert item["part_family_id"] == UNKNOWN_PART_FAMILY_ID
    assert item["experimental_mark"] == EXPERIMENTAL_MARK_TEXT
    detail = client.get(f"/part-drawings/{item['id']}").json()
    listed = next(
        row for row in client.get("/part-drawings").json()["items"] if row["id"] == item["id"]
    )
    assert detail["experimental_mark"] == EXPERIMENTAL_MARK_TEXT
    assert listed["experimental_mark"] == EXPERIMENTAL_MARK_TEXT


def test_带实验性标记的零件图仍可完成复核(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-NQ-01.png").json()["items"][0]
    drawing_id = item["id"]
    assert item["experimental_mark"] == EXPERIMENTAL_MARK_TEXT
    assert item["status"] == "已提取"

    for key in HIGH_RISK_KEYS:
        confirmed = client.post(f"/part-drawings/{drawing_id}/fields/{key}/confirm")
        assert confirmed.status_code == 200
        assert confirmed.json()["experimental_mark"] == EXPERIMENTAL_MARK_TEXT

    done = client.post(f"/part-drawings/{drawing_id}/complete-review")
    assert done.status_code == 200
    body = done.json()
    assert body["status"] == "已复核"
    assert body["experimental_mark"] == EXPERIMENTAL_MARK_TEXT
    assert body["is_target_part_family"] is False
