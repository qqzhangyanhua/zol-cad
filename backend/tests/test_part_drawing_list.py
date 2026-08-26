from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from helpers import create_factory, create_quoter, login


def test_报价员登录后看到空的零件图列表(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()

    assert login(client, "quoter_a", "secret-a").status_code == 200
    response = client.get("/part-drawings")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_登录后能读取当前报价员与所属工厂(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()

    assert login(client, "quoter_a", "secret-a").status_code == 200
    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "username": "quoter_a",
        "factory_name": "华东精密",
        "role": "quoter",
    }


def test_启动时真实执行了Alembic迁移(migrated_engine: Engine) -> None:
    from sqlalchemy import text

    with migrated_engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert version == "0012_stashed_extracted_fields"
