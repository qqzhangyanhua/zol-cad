from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from helpers import create_factory, create_quoter, login


def test_报价员能用账号密码登录(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()

    response = login(client, "quoter_a", "secret-a")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert client.cookies.get("qa_session")


def test_错误密码不能登录(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()

    response = login(client, "quoter_a", "wrong-password")

    assert response.status_code == 401
    assert response.json()["detail"] == "账号或密码不正确"
    assert client.cookies.get("qa_session") is None


def test_未登录不能读取零件图列表(client: TestClient) -> None:
    response = client.get("/part-drawings")
    assert response.status_code == 401


def test_退出登录后不能再读取零件图列表(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()

    assert login(client, "quoter_a", "secret-a").status_code == 200
    assert client.get("/part-drawings").status_code == 200

    logout = client.post("/auth/logout")
    assert logout.status_code == 200

    blocked = client.get("/part-drawings")
    assert blocked.status_code == 401
