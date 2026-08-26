from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, login
from quote_assistant.adapter.extraction.fake import FixtureExtractionEngine
from quote_assistant.adapter.extraction.fixtures import DIRTY_ENGINE_PAYLOAD
from quote_assistant.adapter.extraction.validation import parse_engine_result
from quote_assistant.domain.extraction import (
    ExtractedField,
    ExtractionRequest,
    ExtractionResult,
    FieldCategory,
)
from quote_assistant.domain.quality import QualityGrade


class _CountingEngine:
    def __init__(self, inner: object) -> None:
        self._inner = inner
        self.extract_calls = 0

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        self.extract_calls += 1
        return self._inner.extract(request)


class _CountingStorage:
    def __init__(self, inner: object) -> None:
        self._inner = inner
        self.fetch_calls = 0

    def fetch(self, key: str) -> bytes:
        self.fetch_calls += 1
        return self._inner.fetch(key)

    def __getattr__(self, name: str) -> object:
        return getattr(self._inner, name)


class _CountingRenderer:
    def __init__(self, inner: object) -> None:
        self._inner = inner
        self.render_calls = 0

    def render(self, content: bytes, media_type: str, selected_page: int):
        self.render_calls += 1
        return self._inner.render(content, media_type, selected_page)


class _PoorWithFieldsEngine:
    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        del request
        return ExtractionResult(
            quality_grade=QualityGrade.POOR,
            is_assembly_or_exploded=False,
            fields=(
                ExtractedField(
                    "drawing_no",
                    "图号",
                    "POOR-STASH-01",
                    FieldCategory.TITLE_BLOCK,
                ),
            ),
        )


class _AlwaysDirtyEngine:
    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        del request
        return parse_engine_result(DIRTY_ENGINE_PAYLOAD)


def _login_quoter(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200


def _install_counters(app, inner_engine: object) -> tuple[_CountingEngine, _CountingStorage, _CountingRenderer]:
    engine = _CountingEngine(inner_engine)
    storage = _CountingStorage(app.state.object_storage)
    renderer = _CountingRenderer(app.state.drawing_page_renderer)
    app.state.extraction_engine = engine
    app.state.object_storage = storage
    app.state.drawing_page_renderer = renderer
    return engine, storage, renderer


def _field_value(item: dict, key: str) -> str | None:
    return next(field["value"] for field in item["extracted_fields"] if field["key"] == key)


def test_清晰图从上传到已提取只调一次提取引擎且原图只取回栅格化一次(
    app, client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    engine, storage, renderer = _install_counters(app, FixtureExtractionEngine())

    uploaded = client.post(
        "/part-drawings",
        files=[("files", ("FX-TQ-01.png", PNG_1X1, "image/png"))],
    )
    assert uploaded.status_code == 200
    item = uploaded.json()["items"][0]
    assert item["status"] == "已提取"
    assert item["quality_grade"] == "清晰"
    assert _field_value(item, "drawing_no") == "FL-001"

    assert engine.extract_calls == 1
    assert storage.fetch_calls == 1
    assert renderer.render_calls == 1

    events = client.get(f"/part-drawings/{item['id']}/events").json()["items"]
    assert [row["to_status"] for row in events] == [
        "已上传",
        "分级中",
        "已分级",
        "提取中",
        "已提取",
    ]


def test_差图仍然继续复用首次取数不增加引擎调用(
    app, client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    engine, storage, renderer = _install_counters(app, _PoorWithFieldsEngine())

    uploaded = client.post(
        "/part-drawings",
        files=[("files", ("糊图.png", PNG_1X1, "image/png"))],
    )
    assert uploaded.status_code == 200
    item = uploaded.json()["items"][0]
    assert item["status"] == "建议人工"
    assert item["quality_grade"] == "差"
    assert _field_value(item, "drawing_no") is None
    assert engine.extract_calls == 1
    assert storage.fetch_calls == 1
    assert renderer.render_calls == 1

    continued = client.post(f"/part-drawings/{item['id']}/continue-despite-quality")
    assert continued.status_code == 200
    body = continued.json()
    assert body["status"] == "已提取"
    assert body["low_quality_unreliable"] is True
    assert _field_value(body, "drawing_no") == "POOR-STASH-01"
    assert engine.extract_calls == 1
    assert storage.fetch_calls == 1
    assert renderer.render_calls == 1


def test_装配图一次调用后丢弃字段且没有仍然继续入口(
    app, client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    engine, storage, renderer = _install_counters(app, FixtureExtractionEngine())

    uploaded = client.post(
        "/part-drawings",
        files=[("files", ("FX-ASM-01.png", PNG_1X1, "image/png"))],
    )
    assert uploaded.status_code == 200
    item = uploaded.json()["items"][0]
    assert item["status"] == "不在范围"
    assert item["is_assembly_or_exploded"] is True
    assert all(field["value"] is None for field in item["extracted_fields"])
    assert engine.extract_calls == 1
    assert storage.fetch_calls == 1
    assert renderer.render_calls == 1

    blocked = client.post(f"/part-drawings/{item['id']}/continue-despite-quality")
    assert blocked.status_code == 409
    assert engine.extract_calls == 1


def test_分级失败重试仍从分级开始不跳过劝退(
    app, client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    engine, storage, renderer = _install_counters(app, _AlwaysDirtyEngine())

    uploaded = client.post(
        "/part-drawings",
        files=[("files", ("FX-TQ-01.png", PNG_1X1, "image/png"))],
    )
    assert uploaded.status_code == 200
    item = uploaded.json()["items"][0]
    assert item["status"] == "提取失败"
    assert item["quality_grade"] is None
    assert all(field["value"] is None for field in item["extracted_fields"])
    assert engine.extract_calls == 1

    events = client.get(f"/part-drawings/{item['id']}/events").json()["items"]
    assert [row["to_status"] for row in events] == ["已上传", "分级中", "提取失败"]

    app.state.extraction_engine = engine
    engine._inner = FixtureExtractionEngine()
    retried = client.post(f"/part-drawings/{item['id']}/extract")
    assert retried.status_code == 200
    body = retried.json()
    assert body["status"] == "已提取"
    assert body["quality_grade"] == "清晰"
    assert _field_value(body, "drawing_no") == "FL-001"
    assert engine.extract_calls == 2
    assert storage.fetch_calls == 2
    assert renderer.render_calls == 2

    after = client.get(f"/part-drawings/{item['id']}/events").json()["items"]
    assert [row["to_status"] for row in after] == [
        "已上传",
        "分级中",
        "提取失败",
        "分级中",
        "已分级",
        "提取中",
        "已提取",
    ]
