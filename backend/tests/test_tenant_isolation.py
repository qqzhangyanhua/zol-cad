from __future__ import annotations

import inspect

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from quote_assistant.usecase.continue_despite_poor_quality import ContinueDespitePoorQuality
from quote_assistant.usecase.extract_part_drawing import ExtractPartDrawing
from quote_assistant.usecase.get_part_drawing import GetPartDrawing
from quote_assistant.usecase.issue_original_access_url import IssueOriginalAccessUrl
from quote_assistant.usecase.list_part_drawing_events import ListPartDrawingEvents
from quote_assistant.usecase.list_part_drawings import ListPartDrawings
from quote_assistant.usecase.review_part_drawing import (
    CompleteReview,
    ConfirmExtractedField,
    UpdateExtractedField,
)
from quote_assistant.usecase.upload_part_drawings import UploadPartDrawings
from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, insert_part_drawing, login


def test_列出零件图用例不接受工厂标识参数() -> None:
    signature = inspect.signature(ListPartDrawings.execute)
    assert "factory_id" not in signature.parameters
    assert "tenant_id" not in signature.parameters
    assert list(signature.parameters) == ["self"]


def test_甲厂报价员读不到乙厂的零件图(client: TestClient, db_session: Session) -> None:
    factory_a = create_factory(db_session, "华东精密")
    factory_b = create_factory(db_session, "南方模具")
    create_quoter(db_session, factory_a, "quoter_a", "secret-a")
    create_quoter(db_session, factory_b, "quoter_b", "secret-b")
    drawing_b = insert_part_drawing(db_session, factory_b, "乙厂-轴套.pdf")
    db_session.commit()

    assert login(client, "quoter_a", "secret-a").status_code == 200
    as_a = client.get("/part-drawings")
    assert as_a.status_code == 200
    assert as_a.json() == {"items": []}

    client.post("/auth/logout")
    assert login(client, "quoter_b", "secret-b").status_code == 200
    as_b = client.get("/part-drawings")
    assert as_b.status_code == 200
    items = as_b.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == str(drawing_b)
    assert items[0]["original_filename"] == "乙厂-轴套.pdf"


def test_零件图列表忽略调用方传入的工厂标识(client: TestClient, db_session: Session) -> None:
    factory_a = create_factory(db_session, "华东精密")
    factory_b = create_factory(db_session, "南方模具")
    create_quoter(db_session, factory_a, "quoter_a", "secret-a")
    insert_part_drawing(db_session, factory_b, "乙厂-法兰.pdf")
    db_session.commit()

    assert login(client, "quoter_a", "secret-a").status_code == 200
    response = client.get(
        "/part-drawings",
        params={"factory_id": str(factory_b), "tenant_id": str(factory_b)},
    )

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_上传与查看原图用例不接受工厂标识参数() -> None:
    for cls in (
        UploadPartDrawings,
        GetPartDrawing,
        IssueOriginalAccessUrl,
        ContinueDespitePoorQuality,
        ExtractPartDrawing,
        ListPartDrawingEvents,
        ConfirmExtractedField,
        UpdateExtractedField,
        CompleteReview,
    ):
        names = list(inspect.signature(cls.execute).parameters)
        assert "factory_id" not in names
        assert "tenant_id" not in names


def test_甲厂报价员看不到乙厂刚上传的零件图也不能拿原图临时URL(
    client: TestClient, db_session: Session
) -> None:
    factory_a = create_factory(db_session, "华东精密")
    factory_b = create_factory(db_session, "南方模具")
    create_quoter(db_session, factory_a, "quoter_a", "secret-a")
    create_quoter(db_session, factory_b, "quoter_b", "secret-b")
    db_session.commit()

    assert login(client, "quoter_b", "secret-b").status_code == 200
    uploaded = client.post(
        "/part-drawings",
        files=[("files", ("乙厂-法兰.png", PNG_1X1, "image/png"))],
    )
    assert uploaded.status_code == 200
    drawing_id = uploaded.json()["items"][0]["id"]

    client.post("/auth/logout")
    assert login(client, "quoter_a", "secret-a").status_code == 200
    assert client.get("/part-drawings").json() == {"items": []}
    assert client.get(f"/part-drawings/{drawing_id}").status_code == 404
    assert client.get(f"/part-drawings/{drawing_id}/original").status_code == 404
    assert client.get(f"/part-drawings/{drawing_id}/events").status_code == 404
    assert client.post(f"/part-drawings/{drawing_id}/continue-despite-quality").status_code == 404
    assert client.post(f"/part-drawings/{drawing_id}/extract").status_code == 404
    assert client.post(f"/part-drawings/{drawing_id}/fields/drawing_no/confirm").status_code == 404
    assert (
        client.patch(
            f"/part-drawings/{drawing_id}/fields/drawing_no",
            json={"value": "偷改"},
        ).status_code
        == 404
    )
    assert client.post(f"/part-drawings/{drawing_id}/complete-review").status_code == 404
