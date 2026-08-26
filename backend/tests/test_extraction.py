from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, login
from quote_assistant.adapter.extraction.fake import FixtureExtractionEngine
from quote_assistant.adapter.extraction.fixtures import DIRTY_ENGINE_PAYLOAD
from quote_assistant.adapter.extraction.validation import parse_engine_result
from quote_assistant.domain.extraction import (
    LOOK_AT_DRAWING_DISCLAIMER,
    ExtractionRequest,
    ExtractionResult,
)


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


def _fields_by_key(item: dict) -> dict[str, dict]:
    return {field["key"]: field for field in item["extracted_fields"]}


def _grouped_categories(item: dict) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for field in item["extracted_fields"]:
        grouped.setdefault(field["category"], []).append(field["label"])
    return grouped


class _AlwaysDirtyEngine:
    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        del request
        return parse_engine_result(DIRTY_ENGINE_PAYLOAD)


def test_分级完成后自动读图取数并按类别返回标题栏关键尺寸与技术要求(
    client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    uploaded = _upload(client, "FX-TQ-01.png")
    assert uploaded.status_code == 200
    item = uploaded.json()["items"][0]

    assert item["status"] == "已提取"
    assert item["look_at_drawing_disclaimer"] == LOOK_AT_DRAWING_DISCLAIMER
    assert item["extraction_failure_reason"] is None

    fields = _fields_by_key(item)
    assert fields["drawing_no"]["value"] == "FL-001"
    assert fields["part_name"]["value"] == "法兰"
    assert fields["material"]["value"] == "45#"
    assert fields["quantity"]["value"] == "2"
    assert fields["tightest_tolerance"]["value"] == "IT7"
    assert fields["max_envelope"]["value"] == "Ø120"
    assert fields["roughness"]["value"] == "Ra3.2"

    grouped = _grouped_categories(item)
    assert grouped["标题栏"] == ["图号", "零件名称", "材料", "数量"]
    assert grouped["关键尺寸"] == ["最严公差", "最大外形", "最深孔", "最薄壁"]
    assert grouped["技术要求"] == ["热处理", "表面处理", "粗糙度"]

    events = client.get(f"/part-drawings/{item['id']}/events").json()["items"]
    assert [row["to_status"] for row in events] == [
        "已上传",
        "分级中",
        "已分级",
        "提取中",
        "已提取",
    ]


def test_图上没有的字段如实留空不编造值(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    clear = _upload(client, "FX-TQ-01.png").json()["items"][0]
    average = _upload(client, "FX-TA-01.png").json()["items"][0]
    unknown = _upload(client, "随机零件.png").json()["items"][0]

    clear_fields = _fields_by_key(clear)
    assert clear_fields["deepest_hole"]["value"] is None
    assert clear_fields["thinnest_wall"]["value"] is None
    assert clear_fields["heat_treatment"]["value"] is None
    assert clear_fields["surface_treatment"]["value"] is None

    average_fields = _fields_by_key(average)
    assert average["status"] == "已提取"
    assert average_fields["drawing_no"]["value"] == "XT-018"
    assert average_fields["material"]["value"] is None
    assert average_fields["thinnest_wall"]["value"] is None
    assert average_fields["heat_treatment"]["value"] is None
    assert average_fields["roughness"]["value"] is None
    assert average_fields["deepest_hole"]["value"] == "Ø8×40"
    assert average_fields["surface_treatment"]["value"] == "发黑"

    unknown_fields = _fields_by_key(unknown)
    assert unknown["status"] == "已提取"
    assert all(field["value"] is None for field in unknown_fields.values())
    assert set(unknown_fields) == {
        "drawing_no",
        "part_name",
        "material",
        "quantity",
        "tightest_tolerance",
        "max_envelope",
        "deepest_hole",
        "thinnest_wall",
        "heat_treatment",
        "surface_treatment",
        "roughness",
    }


def test_差图不自动预填因此没有提取结果(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TP-01.png").json()["items"][0]
    assert item["status"] == "建议人工"
    assert all(field["value"] is None for field in item["extracted_fields"])
    assert item["extraction_failure_reason"] is None
    events = client.get(f"/part-drawings/{item['id']}/events").json()["items"]
    assert [row["to_status"] for row in events] == ["已上传", "分级中", "建议人工"]


def test_适配器校验失败按提取失败处理脏数据不进领域层(
    app, client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    app.state.extraction_engine = _AlwaysDirtyEngine()
    uploaded = _upload(client, "FX-TQ-01.png")
    assert uploaded.status_code == 200
    item = uploaded.json()["items"][0]

    assert item["status"] == "提取失败"
    assert item["quality_grade"] is None
    assert (
        item["extraction_failure_reason"] == "提取引擎返回结果未通过适配器校验，脏数据未进入领域层"
    )
    assert item["look_at_drawing_disclaimer"] == LOOK_AT_DRAWING_DISCLAIMER
    assert all(field["value"] is None for field in item["extracted_fields"])
    assert all("invented_confidence" not in field for field in item["extracted_fields"])
    assert all(field["value"] != 12345 for field in item["extracted_fields"])

    events = client.get(f"/part-drawings/{item['id']}/events").json()["items"]
    assert [row["to_status"] for row in events][-2:] == ["分级中", "提取失败"]


def test_提取失败可一键重试且不必重新上传(app, client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    app.state.extraction_engine = _AlwaysDirtyEngine()
    drawing_id = _upload(client, "FX-TQ-01.png").json()["items"][0]["id"]
    assert client.get(f"/part-drawings/{drawing_id}").json()["status"] == "提取失败"
    assert client.get(f"/part-drawings/{drawing_id}").json()["quality_grade"] is None

    app.state.extraction_engine = FixtureExtractionEngine()
    retried = client.post(f"/part-drawings/{drawing_id}/extract")
    assert retried.status_code == 200
    body = retried.json()
    assert body["status"] == "已提取"
    assert body["extraction_failure_reason"] is None
    assert _fields_by_key(body)["drawing_no"]["value"] == "FL-001"
    assert _fields_by_key(body)["deepest_hole"]["value"] is None

    events = client.get(f"/part-drawings/{drawing_id}/events").json()["items"]
    assert [row["to_status"] for row in events] == [
        "已上传",
        "分级中",
        "提取失败",
        "分级中",
        "已分级",
        "提取中",
        "已提取",
    ]


def test_已提取后可重试读图取数(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    drawing_id = _upload(client, "FX-TQ-01.png").json()["items"][0]["id"]
    response = client.post(f"/part-drawings/{drawing_id}/extract")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "已提取"
    assert _fields_by_key(body)["drawing_no"]["value"] == "FL-001"


def test_看图提示常驻在提取结果里(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TQ-01.png").json()["items"][0]
    detail = client.get(f"/part-drawings/{item['id']}").json()
    listed = client.get("/part-drawings").json()["items"][0]
    assert detail["look_at_drawing_disclaimer"] == LOOK_AT_DRAWING_DISCLAIMER
    assert listed["look_at_drawing_disclaimer"] == LOOK_AT_DRAWING_DISCLAIMER


def test_脏引擎重试仍失败时不写入编造字段(app, client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    app.state.extraction_engine = _AlwaysDirtyEngine()
    drawing_id = _upload(client, "FX-TQ-01.png").json()["items"][0]["id"]
    app.state.extraction_engine = _AlwaysDirtyEngine()
    retried = client.post(f"/part-drawings/{drawing_id}/extract")
    assert retried.status_code == 200
    body = retried.json()
    assert body["status"] == "提取失败"
    assert "脏数据未进入领域层" in body["extraction_failure_reason"]
    assert all(field["value"] is None for field in body["extracted_fields"])
