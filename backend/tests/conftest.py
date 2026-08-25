from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from quote_assistant.adapter.db.session import make_engine
from quote_assistant.config import Settings
from quote_assistant.interface.http.app import create_app

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _normalize_postgres_url(url: str) -> str:
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql+psycopg2://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(
            ["docker", "info"],
            check=False,
            capture_output=True,
            timeout=8,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _start_postgres_container() -> tuple[str, object]:
    from testcontainers.postgres import PostgresContainer

    container = PostgresContainer("postgres:16-alpine")
    container.start()
    url = _normalize_postgres_url(container.get_connection_url())
    return url, container


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    """Real Postgres: prefer an explicit URL (CI service container), else testcontainers."""
    explicit = os.environ.get("QA_TEST_DATABASE_URL")
    if explicit:
        url = _normalize_postgres_url(explicit)
        yield url
        return
    if not _docker_available():
        raise RuntimeError(
            "缝 1 需要容器化的真实 Postgres。请启动 compose.yaml 中的 postgres，"
            "或设置 QA_TEST_DATABASE_URL，或在本机提供 Docker 以便 testcontainers 拉起 Postgres。"
        )
    url, container = _start_postgres_container()
    try:
        yield url
    finally:
        container.stop()


@pytest.fixture(scope="session")
def migrated_engine(database_url: str) -> Iterator[Engine]:
    alembic_cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")
    engine = make_engine(database_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def object_store_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("object-store")


@pytest.fixture(scope="session")
def app(database_url: str, migrated_engine: Engine, object_store_dir: Path):
    del migrated_engine  # migrations must run before the app starts
    settings = Settings(
        database_url=database_url,
        seed_demo_data=False,
        object_store_backend="local",
        local_object_dir=str(object_store_dir),
        public_base_url="",
        object_sign_secret="test-object-sign-secret",
        signed_url_ttl_seconds=300,
    )
    return create_app(settings)


@pytest.fixture(autouse=True)
def clean_object_store(object_store_dir: Path) -> Iterator[None]:
    yield
    for child in object_store_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


@pytest.fixture
def client(app) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session(migrated_engine: Engine) -> Iterator[Session]:
    factory = sessionmaker(bind=migrated_engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
        session.commit()
    finally:
        session.close()


@pytest.fixture(autouse=True)
def truncate_tables(migrated_engine: Engine) -> Iterator[None]:
    with migrated_engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE sessions, manual_baselines, correction_records, part_drawing_events, "
                "part_drawings, quote_tasks, quote_sheet_templates, factory_preferences, "
                "users, factories "
                "RESTART IDENTITY CASCADE"
            )
        )
    yield
