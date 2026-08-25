from __future__ import annotations

import inspect

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from quote_assistant.usecase.list_part_drawings import ListPartDrawings
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
