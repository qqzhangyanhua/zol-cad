from __future__ import annotations

import struct
from io import BytesIO

from fastapi.testclient import TestClient
from pypdf import PdfWriter
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, login
from quote_assistant.adapter.extraction.fake import FixtureExtractionEngine
from quote_assistant.domain.extraction import ExtractionRequest, ExtractionResult


class _RecordingEngine:
    """Wraps the fixture engine and keeps what actually reached the 提取引擎 Port."""

    def __init__(self) -> None:
        self._inner = FixtureExtractionEngine()
        self.requests: list[ExtractionRequest] = []

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        self.requests.append(request)
        return self._inner.extract(request)


def _pdf_with_page_shapes(shapes: list[tuple[int, int]]) -> bytes:
    writer = PdfWriter()
    for width, height in shapes:
        writer.add_blank_page(width=width, height=height)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _png_size(content: bytes) -> tuple[int, int]:
    assert content.startswith(b"\x89PNG\r\n\x1a\n")
    width, height = struct.unpack(">II", content[16:24])
    return width, height


def _login_quoter(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200


def test_多页PDF只把报价员指定的那一页送进提取引擎(
    app, client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    engine = _RecordingEngine()
    app.state.extraction_engine = engine
    # 第 1 页是正方形，第 2 页是 4:1 的宽幅，渲染出来的图形状足以区分送进去的是哪一页。
    pdf = _pdf_with_page_shapes([(200, 200), (400, 100)])

    uploaded = client.post(
        "/part-drawings",
        files=[("files", ("FX-TQ-01.pdf", pdf, "application/pdf"))],
        data={"selected_pages": "[2]"},
    )
    assert uploaded.status_code == 200
    item = uploaded.json()["items"][0]
    assert item["status"] == "已提取"
    assert item["selected_page"] == 2

    assert engine.requests, "提取引擎一次都没有被调用"
    for request in engine.requests:
        assert request.media_type == "image/png"
        width, height = _png_size(request.page_content)
        assert width > height, "送进引擎的不是第 2 页"
        assert round(width / height) == 4


def test_图片上传时内容与媒体类型原样透传(app, client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    engine = _RecordingEngine()
    app.state.extraction_engine = engine

    uploaded = client.post(
        "/part-drawings",
        files=[("files", ("FX-TQ-01.png", PNG_1X1, "image/png"))],
    )
    assert uploaded.status_code == 200

    assert engine.requests
    for request in engine.requests:
        assert request.media_type == "image/png"
        assert request.page_content == PNG_1X1


def test_选定页渲染失败按提取失败处理且可重试(app, client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200

    pdf = _pdf_with_page_shapes([(200, 200)])
    uploaded = client.post(
        "/part-drawings",
        files=[("files", ("FX-TQ-01.pdf", pdf, "application/pdf"))],
    )
    assert uploaded.status_code == 200
    drawing_id = uploaded.json()["items"][0]["id"]

    storage_key = f"part-drawings/{factory_id}/{drawing_id}/original.pdf"
    app.state.object_storage.store(storage_key, b"%PDF-1.4 truncated", "application/pdf")

    failed = client.post(f"/part-drawings/{drawing_id}/extract")
    assert failed.status_code == 200
    body = failed.json()
    assert body["status"] == "提取失败"
    assert "无法打开" in body["extraction_failure_reason"]

    app.state.object_storage.store(storage_key, pdf, "application/pdf")
    retried = client.post(f"/part-drawings/{drawing_id}/extract")
    assert retried.status_code == 200
    assert retried.json()["status"] == "已提取"
    assert retried.json()["extraction_failure_reason"] is None
