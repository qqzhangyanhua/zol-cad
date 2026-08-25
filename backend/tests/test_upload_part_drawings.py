from __future__ import annotations

import inspect
from datetime import UTC, datetime
from urllib.parse import urlparse

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1, make_pdf
from helpers import create_factory, create_quoter, login
from quote_assistant.domain.drawing_upload import MAX_FILE_BYTES, MAX_FILE_SIZE_MB, MAX_PDF_PAGES
from quote_assistant.usecase.upload_part_drawings import UploadPartDrawings


def _upload(
    client: TestClient,
    files: list[tuple[str, bytes, str]],
    selected_pages: list[int] | None = None,
):
    multipart = [("files", (name, content, content_type)) for name, content, content_type in files]
    data = None
    if selected_pages is not None:
        import json

        data = {"selected_pages": json.dumps(selected_pages)}
    return client.post("/part-drawings", files=multipart, data=data)


def test_上传零件图用例不接受工厂标识参数() -> None:
    signature = inspect.signature(UploadPartDrawings.execute)
    assert "factory_id" not in signature.parameters
    assert "tenant_id" not in signature.parameters
    assert list(signature.parameters) == ["self", "files"]


def test_报价员能上传单张PDF零件图并出现在列表(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200

    before = datetime.now(UTC)
    pdf = make_pdf(pages=1)
    uploaded = _upload(client, [("法兰.pdf", pdf, "application/pdf")])
    after = datetime.now(UTC)

    assert uploaded.status_code == 200
    body = uploaded.json()
    assert body["rejected"] == []
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["original_filename"] == "法兰.pdf"
    assert item["content_type"] == "application/pdf"
    assert item["page_count"] == 1
    assert item["selected_page"] == 1
    uploaded_at = datetime.fromisoformat(item["uploaded_at"])
    assert before <= uploaded_at <= after

    listed = client.get("/part-drawings")
    assert listed.status_code == 200
    assert listed.json()["items"][0]["id"] == item["id"]
    assert listed.json()["items"][0]["original_filename"] == "法兰.pdf"


def test_报价员能上传常见图片零件图(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200

    uploaded = _upload(client, [("轴套.png", PNG_1X1, "image/png")])
    assert uploaded.status_code == 200
    item = uploaded.json()["items"][0]
    assert item["original_filename"] == "轴套.png"
    assert item["content_type"] == "image/png"
    assert item["page_count"] == 1


def test_能一次批量上传多张零件图(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200

    uploaded = _upload(
        client,
        [
            ("法兰.pdf", make_pdf(1), "application/pdf"),
            ("轴套.png", PNG_1X1, "image/png"),
        ],
    )
    assert uploaded.status_code == 200
    names = {item["original_filename"] for item in uploaded.json()["items"]}
    assert names == {"法兰.pdf", "轴套.png"}
    listed = client.get("/part-drawings")
    assert {item["original_filename"] for item in listed.json()["items"]} == names


def test_超出单文件大小上限被拒绝并写明限制数值(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200

    oversized = b"%PDF-1.4\n" + b"x" * (MAX_FILE_BYTES + 1)
    uploaded = _upload(client, [("过大.pdf", oversized, "application/pdf")])
    assert uploaded.status_code == 200
    assert uploaded.json()["items"] == []
    detail = uploaded.json()["rejected"][0]["detail"]
    assert "单文件大小上限" in detail
    assert f"{MAX_FILE_SIZE_MB} MB" in detail
    assert client.get("/part-drawings").json() == {"items": []}


def test_超出PDF页数上限被拒绝并写明限制数值(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200

    too_many = make_pdf(pages=MAX_PDF_PAGES + 1)
    uploaded = _upload(client, [("手册.pdf", too_many, "application/pdf")])
    assert uploaded.status_code == 200
    detail = uploaded.json()["rejected"][0]["detail"]
    assert "PDF 页数上限" in detail
    assert f"{MAX_PDF_PAGES} 页" in detail
    assert f"{MAX_PDF_PAGES + 1} 页" in detail
    assert client.get("/part-drawings").json() == {"items": []}


def test_不支持的格式被拒绝(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200

    uploaded = _upload(client, [("说明.txt", b"hello", "text/plain")])
    assert uploaded.status_code == 200
    detail = uploaded.json()["rejected"][0]["detail"]
    assert "不是 PDF 或常见图片" in detail
    assert "PDF" in detail


def test_多页PDF默认处理第1页且报价员能改指定页(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200

    pdf = make_pdf(pages=3)
    defaulted = _upload(client, [("多页.pdf", pdf, "application/pdf")])
    assert defaulted.status_code == 200
    assert defaulted.json()["items"][0]["selected_page"] == 1
    assert defaulted.json()["items"][0]["page_count"] == 3

    chosen = _upload(client, [("多页-第2页.pdf", pdf, "application/pdf")], selected_pages=[2])
    assert chosen.status_code == 200
    assert chosen.json()["items"][0]["selected_page"] == 2
    assert chosen.json()["items"][0]["page_count"] == 3


def test_批量中不合格文件被拒绝合格文件仍入库(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200

    uploaded = _upload(
        client,
        [
            ("轴套.png", PNG_1X1, "image/png"),
            ("说明.txt", b"hello", "text/plain"),
        ],
    )
    assert uploaded.status_code == 200
    assert [item["original_filename"] for item in uploaded.json()["items"]] == ["轴套.png"]
    assert uploaded.json()["rejected"][0]["original_filename"] == "说明.txt"


def test_原图通过短时效临时URL访问且内容一致(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200

    png = PNG_1X1
    uploaded = _upload(client, [("轴套.png", png, "image/png")])
    drawing_id = uploaded.json()["items"][0]["id"]

    access = client.get(f"/part-drawings/{drawing_id}/original")
    assert access.status_code == 200
    url = access.json()["url"]
    assert "sig=" in url
    parsed = urlparse(url)
    path = parsed.path if parsed.path.startswith("/") else url
    query = f"?{parsed.query}" if parsed.query else ""
    fetched = client.get(f"{path}{query}")
    assert fetched.status_code == 200
    assert fetched.content == png
    assert fetched.headers["content-type"].startswith("image/png")


def test_缺少签名的对象存储地址不能读取(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200
    uploaded = _upload(client, [("轴套.png", PNG_1X1, "image/png")])
    drawing_id = uploaded.json()["items"][0]["id"]
    access = client.get(f"/part-drawings/{drawing_id}/original")
    parsed = urlparse(access.json()["url"])
    blocked = client.get(parsed.path)
    assert blocked.status_code == 403
