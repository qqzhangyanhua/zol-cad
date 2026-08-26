from __future__ import annotations

import asyncio
import logging
import threading
import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, login
from quote_assistant.adapter.db.repositories import (
    SqlPartDrawingEventRepository,
    SqlPartDrawingRepository,
)
from quote_assistant.adapter.db.session import SqlAlchemyUnitOfWork
from quote_assistant.adapter.extraction.cost import ExtractionCostEvent, InMemoryExtractionCostCounter
from quote_assistant.adapter.extraction.fake import FixtureExtractionEngine
from quote_assistant.config import Settings, validate_runtime_settings
from quote_assistant.domain.entities import Actor, PartDrawingStatus, Role
from quote_assistant.domain.errors import IllegalPartDrawingTransition, PartDrawingNotFound
from quote_assistant.domain.part_drawing_state import PartDrawingEvent
from quote_assistant.interface.http.app import create_app
from quote_assistant.interface.http.background import (
    ProcessPartDrawingJob,
    ThreadPartDrawingProcessor,
    normalize_part_drawing_processor,
)
from quote_assistant.interface.http.uploads import read_upload_bounded
from quote_assistant.usecase.process_part_drawing import ProcessPartDrawing
from quote_assistant.usecase.recover_stranded_part_drawings import RecoverStrandedPartDrawings


def _actor(user_id: UUID, factory_id: UUID) -> Actor:
    return Actor(
        user_id=user_id,
        factory_id=factory_id,
        factory_name="华东精密",
        username="quoter_a",
        role=Role.QUOTER,
    )


def _login_quoter(client: TestClient, db_session: Session) -> tuple[UUID, UUID]:
    factory_id = create_factory(db_session, "华东精密")
    user_id = create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200
    return factory_id, user_id


def test_本地环境允许占位密钥() -> None:
    validate_runtime_settings(Settings())


def test_生产环境拒绝占位签名密钥与demo密码() -> None:
    with pytest.raises(RuntimeError, match="OBJECT_SIGN_SECRET"):
        create_app(Settings(app_env="production"))
    with pytest.raises(RuntimeError, match="DEMO_PASSWORD_A"):
        create_app(
            Settings(
                app_env="production",
                object_sign_secret="not-the-default-secret",
            )
        )
    with pytest.raises(RuntimeError, match="SESSION_COOKIE_SECURE|Secure"):
        create_app(
            Settings(
                app_env="production",
                object_sign_secret="not-the-default-secret",
                demo_password_a="real-a",
                demo_password_b="real-b",
                session_cookie_secure=False,
            )
        )


def test_生产环境覆盖占位值后通过校验() -> None:
    validate_runtime_settings(
        Settings(
            app_env="production",
            object_sign_secret="not-the-default-secret",
            demo_password_a="real-a",
            demo_password_b="real-b",
        )
    )


def test_未知零件图作业实现抛错() -> None:
    with pytest.raises(ValueError, match="未知零件图作业实现"):
        normalize_part_drawing_processor("celery")


def test_未知提取引擎仍然抛错() -> None:
    from quote_assistant.adapter.extraction.factory import normalize_extraction_engine

    with pytest.raises(ValueError, match="未知提取引擎"):
        normalize_extraction_engine("mystery")


def test_健康检查连通数据库(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_健康检查数据库不可用返回503(app, client: TestClient) -> None:
    previous = app.state.session_factory

    def boom() -> None:
        raise RuntimeError("db down")

    app.state.session_factory = boom
    try:
        response = client.get("/health")
        assert response.status_code == 503
        assert "数据库" in response.json()["detail"]
    finally:
        app.state.session_factory = previous


def test_未捕获领域错误不会变成500加traceback(app, client: TestClient) -> None:
    @app.get("/__domain-error")
    def _boom() -> None:
        raise PartDrawingNotFound()

    response = client.get("/__domain-error")
    assert response.status_code == 404
    assert "Traceback" not in response.text
    assert "PartDrawingNotFound" in response.text


def test_本地session_cookie不强制secure(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    response = login(client, "quoter_a", "secret-a")
    assert response.status_code == 200
    header = response.headers.get("set-cookie", "")
    assert "qa_session=" in header
    assert "secure" not in header.lower()


def test_生产session_cookie带secure(
    database_url: str, migrated_engine, object_store_dir, db_session: Session
) -> None:
    del migrated_engine
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    settings = Settings(
        app_env="production",
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
        response = login(client, "quoter_a", "secret-a")
        assert response.status_code == 200
        assert "secure" in response.headers.get("set-cookie", "").lower()


def test_线程处理器上传后后台完成(
    app, client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    processor = ThreadPartDrawingProcessor(
        ProcessPartDrawingJob(app),
        workers=1,
        queue_max=4,
    )
    previous = app.state.part_drawing_processor
    app.state.part_drawing_processor = processor
    try:
        uploaded = client.post(
            "/part-drawings",
            files=[("files", ("FX-TQ-01.png", PNG_1X1, "image/png"))],
        )
        assert uploaded.status_code == 200
        item = uploaded.json()["items"][0]
        assert item["status"] == "已上传"
        deadline = time.monotonic() + 8
        status = item["status"]
        while time.monotonic() < deadline:
            status = client.get(f"/part-drawings/{item['id']}").json()["status"]
            if status == "已提取":
                break
            time.sleep(0.05)
        assert status == "已提取"
    finally:
        processor.shutdown()
        app.state.part_drawing_processor = previous


def test_线程处理器失败会记日志(caplog) -> None:
    class _BoomJob:
        def run(self, actor: Actor, drawing_id: UUID) -> None:
            del actor
            raise RuntimeError(f"forced {drawing_id}")

    processor = ThreadPartDrawingProcessor(_BoomJob(), workers=1, queue_max=1)
    actor = _actor(uuid4(), uuid4())
    drawing_id = uuid4()
    try:
        assert processor._slots.acquire(timeout=1)
        with caplog.at_level(logging.ERROR, logger="quote_assistant.background"):
            processor._run_quietly(actor, drawing_id)
        assert "零件图后台处理失败" in caplog.text
        assert str(drawing_id) in caplog.text
    finally:
        processor.shutdown()


def test_作业队列有上界不会无限堆积() -> None:
    class _BlockJob:
        def __init__(self) -> None:
            self.entered = threading.Event()
            self.release = threading.Event()

        def run(self, actor: Actor, drawing_id: UUID) -> None:
            del actor, drawing_id
            self.entered.set()
            self.release.wait(5)

    job = _BlockJob()
    processor = ThreadPartDrawingProcessor(
        job, workers=1, queue_max=1, enqueue_timeout_seconds=0.05
    )
    actor = _actor(uuid4(), uuid4())
    try:
        assert processor.submit(actor, uuid4()) is None
        assert job.entered.wait(2)
        assert processor.submit(actor, uuid4()) is None
        assert processor.submit(actor, uuid4()) is None
    finally:
        job.release.set()
        processor.shutdown()


def test_回收失败不阻止应用启动(
    database_url: str, migrated_engine, object_store_dir, monkeypatch
) -> None:
    del migrated_engine

    def boom(self) -> int:
        del self
        raise RuntimeError("scan failed")

    monkeypatch.setattr(RecoverStrandedPartDrawings, "execute", boom)
    settings = Settings(
        database_url=database_url,
        seed_demo_data=False,
        object_store_backend="local",
        local_object_dir=str(object_store_dir),
        part_drawing_processor="inline",
    )
    with TestClient(create_app(settings)) as client:
        assert client.get("/health").status_code == 200


def test_成本事件列表有上界() -> None:
    counter = InMemoryExtractionCostCounter(max_events=3)
    for index in range(10):
        counter.record(
            ExtractionCostEvent(
                input_drawing_id=f"d{index}",
                page_byte_size=1,
                prompt_template_id="t",
                outcome="ok",
            )
        )
    assert counter.total_calls == 10
    assert len(counter.events) == 3
    assert counter.events[0].input_drawing_id == "d7"
    assert counter.events[-1].input_drawing_id == "d9"


def test_上传超限在读完全文件前中断() -> None:
    from quote_assistant.domain.drawing_upload import MAX_FILE_BYTES

    leftover_read = {"count": 0}

    class _FakeUpload:
        filename = "过大.pdf"

        def __init__(self) -> None:
            self._chunks = [
                b"%PDF-1.4\n",
                b"x" * MAX_FILE_BYTES,
                b"SHOULD-NOT-BE-READ",
            ]

        async def read(self, size: int = -1) -> bytes:
            del size
            if not self._chunks:
                return b""
            chunk = self._chunks.pop(0)
            if chunk == b"SHOULD-NOT-BE-READ":
                leftover_read["count"] += 1
            return chunk

        async def close(self) -> None:
            return None

    result = asyncio.run(read_upload_bounded(_FakeUpload()))
    assert isinstance(result, str)
    assert "单文件大小上限" in result
    assert leftover_read["count"] == 0


def test_请求体过大返回413() -> None:
    from quote_assistant.interface.http.limits import RequestSizeLimitMiddleware

    sent: list[dict[str, object]] = []

    async def inner(scope: dict[str, object], receive: object, send: object) -> None:
        del scope, receive, send
        raise AssertionError("oversized request must not reach the app")

    middleware = RequestSizeLimitMiddleware(inner, max_bytes=32)

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, object]) -> None:
        sent.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [(b"content-length", b"64")],
        "client": ("test", 123),
        "server": ("test", 80),
    }
    asyncio.run(middleware(scope, receive, send))
    start = next(item for item in sent if item["type"] == "http.response.start")
    assert start["status"] == 413


def test_后台作业与重试不会双跑且序号不重复(
    app, client: TestClient, db_session: Session
) -> None:
    factory_id, user_id = _login_quoter(client, db_session)
    from quote_assistant.interface.http.background import DeferredPartDrawingProcessor

    deferred = DeferredPartDrawingProcessor(ProcessPartDrawingJob(app))
    app.state.part_drawing_processor = deferred
    uploaded = client.post(
        "/part-drawings",
        files=[("files", ("FX-TQ-01.png", PNG_1X1, "image/png"))],
    )
    assert uploaded.status_code == 200
    drawing_id = UUID(uploaded.json()["items"][0]["id"])
    assert uploaded.json()["items"][0]["status"] == "已上传"

    started = threading.Barrier(2)
    outcomes: list[object] = []
    lock = threading.Lock()

    class _SlowEngine:
        def __init__(self) -> None:
            self.calls = 0
            self._inner = FixtureExtractionEngine()
            self._lock = threading.Lock()

        def extract(self, request):
            with self._lock:
                self.calls += 1
            time.sleep(0.4)
            return self._inner.extract(request)

    engine = _SlowEngine()
    previous_engine = app.state.extraction_engine
    app.state.extraction_engine = engine
    actor = _actor(user_id, factory_id)

    def _run() -> None:
        session = app.state.session_factory()
        try:
            started.wait(3)
            result = ProcessPartDrawing(
                actor=actor,
                drawings=SqlPartDrawingRepository(session),
                events=SqlPartDrawingEventRepository(session),
                storage=app.state.object_storage,
                renderer=app.state.drawing_page_renderer,
                engine=engine,
                uow=SqlAlchemyUnitOfWork(session),
            ).execute(drawing_id)
            with lock:
                outcomes.append(result.status)
        except IllegalPartDrawingTransition as exc:
            with lock:
                outcomes.append(exc)
        finally:
            session.close()

    try:
        threads = [threading.Thread(target=_run) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(5)
            assert not thread.is_alive()
        assert engine.calls == 1
        statuses = [item for item in outcomes if not isinstance(item, Exception)]
        conflicts = [item for item in outcomes if isinstance(item, IllegalPartDrawingTransition)]
        assert len(statuses) == 1
        assert statuses[0] is PartDrawingStatus.EXTRACTED
        assert len(conflicts) == 1
        events = client.get(f"/part-drawings/{drawing_id}/events").json()["items"]
        sequence_nos = [item["sequence_no"] for item in events]
        assert sequence_nos == sorted(sequence_nos)
        assert len(sequence_nos) == len(set(sequence_nos))
    finally:
        app.state.extraction_engine = previous_engine


def test_并发next_sequence不重复(app, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    user_id = create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    from helpers import insert_part_drawing

    drawing_id = insert_part_drawing(
        db_session,
        factory_id,
        "seq.png",
        status=PartDrawingStatus.UPLOADED,
        uploaded_by_user_id=user_id,
    )
    db_session.commit()

    numbers: list[int] = []
    barrier = threading.Barrier(2)
    lock = threading.Lock()

    def _allocate() -> None:
        session = app.state.session_factory()
        try:
            events = SqlPartDrawingEventRepository(session)
            barrier.wait(3)
            sequence_no = events.next_sequence(drawing_id)
            events.add(
                PartDrawingEvent(
                    id=uuid4(),
                    part_drawing_id=drawing_id,
                    factory_id=factory_id,
                    from_status=None,
                    to_status=PartDrawingStatus.GRADING,
                    occurred_at=datetime.now(UTC),
                    sequence_no=sequence_no,
                    actor_user_id=user_id,
                )
            )
            session.commit()
            with lock:
                numbers.append(sequence_no)
        finally:
            session.close()

    threads = [threading.Thread(target=_allocate) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(5)
        assert not thread.is_alive()
    assert sorted(numbers) == [1, 2]
