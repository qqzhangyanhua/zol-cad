from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, login
from quote_assistant.adapter.extraction.factory import (
    FixtureEngineNotAllowed,
    build_extraction_engine,
)
from quote_assistant.adapter.extraction.fake import FixtureExtractionEngine
from quote_assistant.adapter.extraction.vendor import (
    VENDOR_NOT_CONFIGURED_REASON,
    VendorExtractionEngine,
)
from quote_assistant.config import FIXTURE_ENGINE_FORBIDDEN_MESSAGE, Settings
from quote_assistant.domain.extraction import ExtractionRequest
from quote_assistant.domain.part_family import TARGET_PART_FAMILY_ID, UNKNOWN_PART_FAMILY_ID
from quote_assistant.interface.http.app import create_app


def _request() -> ExtractionRequest:
    return ExtractionRequest(
        page_content=PNG_1X1,
        media_type="image/png",
        part_family_id=TARGET_PART_FAMILY_ID,
        input_drawing_id="我的图-FX-TQ-01.pdf",
    )


def test_local_dev_test允许选择fixture引擎() -> None:
    for env in ("local", "dev", "development", "test"):
        engine = build_extraction_engine(Settings(app_env=env, extraction_engine="fixture"))
        assert isinstance(engine, FixtureExtractionEngine)


def test_非本地环境不能选择fixture引擎() -> None:
    for env in ("production", "prod", "staging", "anything-else"):
        with pytest.raises(FixtureEngineNotAllowed, match="fixture"):
            build_extraction_engine(Settings(app_env=env, extraction_engine="fixture"))


def test_生产环境可以选vendor骨架() -> None:
    engine = build_extraction_engine(Settings(app_env="production", extraction_engine="vendor"))
    assert isinstance(engine, VendorExtractionEngine)


def test_fixture引擎在不允许时既不能构造也不能extract() -> None:
    with pytest.raises(FixtureEngineNotAllowed, match="预置假提取"):
        FixtureExtractionEngine(allowed=False)

    engine = FixtureExtractionEngine(allowed=True)
    engine._allowed = False
    with pytest.raises(FixtureEngineNotAllowed, match="预置假提取"):
        engine.extract(_request())


def test_生产启动拒绝fixture即使密钥已覆盖() -> None:
    with pytest.raises(RuntimeError, match="fixture"):
        create_app(
            Settings(
                app_env="production",
                extraction_engine="fixture",
                object_sign_secret="not-the-default-secret",
                demo_password_a="real-a",
                demo_password_b="real-b",
            )
        )


def test_生产环境文件名不能触发预置假提取(
    database_url: str, migrated_engine, object_store_dir, db_session: Session
) -> None:
    del migrated_engine
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    settings = Settings(
        app_env="production",
        extraction_engine="vendor",
        database_url=database_url,
        seed_demo_data=False,
        object_store_backend="local",
        local_object_dir=str(object_store_dir),
        object_sign_secret="prod-object-sign-secret",
        demo_password_a="prod-a",
        demo_password_b="prod-b",
        session_cookie_secure=True,
        part_drawing_processor="inline",
    )
    with TestClient(create_app(settings)) as client:
        assert login(client, "quoter_a", "secret-a").status_code == 200
        uploaded = client.post(
            "/part-drawings",
            files=[("files", ("我的图-FX-TQ-01.png", PNG_1X1, "image/png"))],
        )
        assert uploaded.status_code == 200
        item = uploaded.json()["items"][0]
        assert item["part_family_id"] == UNKNOWN_PART_FAMILY_ID
        assert item["is_target_part_family"] is False
        assert item["status"] == "提取失败"
        assert item["extraction_failure_reason"] == VENDOR_NOT_CONFIGURED_REASON
        fields = {field["key"]: field["value"] for field in item["extracted_fields"]}
        assert fields.get("drawing_no") != "FL-001"
        assert fields.get("material") != "45#"


def test_禁止信息与启动校验文案一致() -> None:
    assert "文件名不得触发预置假提取结果" in FIXTURE_ENGINE_FORBIDDEN_MESSAGE
