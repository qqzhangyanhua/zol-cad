from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, insert_part_drawing, login
from quote_assistant.adapter.db.repositories import (
    SqlInFlightPartDrawingRepository,
    SqlPartDrawingEventRepository,
)
from quote_assistant.adapter.db.session import SqlAlchemyUnitOfWork
from quote_assistant.adapter.extraction.fake import FixtureExtractionEngine
from quote_assistant.domain.entities import PartDrawingStatus
from quote_assistant.domain.extraction import ExtractionRequest, ExtractionResult
from quote_assistant.interface.http.background import (
    DeferredPartDrawingProcessor,
    ProcessPartDrawingJob,
)
from quote_assistant.usecase.recover_stranded_part_drawings import (
    STRANDED_REASON,
    RecoverStrandedPartDrawings,
)


def _login_quoter(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200


class _FailOnFilenameEngine:
    def __init__(self, failing_name: str) -> None:
        self._inner = FixtureExtractionEngine()
        self._failing_name = failing_name

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        if request.input_drawing_id == self._failing_name:
            raise RuntimeError("forced engine failure")
        return self._inner.extract(request)


def test_延迟作业下上传立刻返回已上传_跑完后变为已提取(
    app, client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    deferred = DeferredPartDrawingProcessor(ProcessPartDrawingJob(app))
    app.state.part_drawing_processor = deferred

    uploaded = client.post(
        "/part-drawings",
        files=[("files", ("FX-TQ-01.png", PNG_1X1, "image/png"))],
    )
    assert uploaded.status_code == 200
    item = uploaded.json()["items"][0]
    assert item["status"] == "已上传"
    assert item["quality_grade"] is None
    assert deferred.pending

    finished = deferred.run_pending()
    assert finished[0].status is PartDrawingStatus.EXTRACTED

    detail = client.get(f"/part-drawings/{item['id']}").json()
    assert detail["status"] == "已提取"
    assert detail["quality_grade"] == "清晰"


def test_同批一张失败不影响另一张已落盘的零件图(
    app, client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    app.state.extraction_engine = _FailOnFilenameEngine("坏图.png")

    uploaded = client.post(
        "/part-drawings",
        files=[
            ("files", ("FX-TQ-01.png", PNG_1X1, "image/png")),
            ("files", ("坏图.png", PNG_1X1, "image/png")),
        ],
    )
    assert uploaded.status_code == 200
    items = uploaded.json()["items"]
    assert len(items) == 2
    by_name = {item["original_filename"]: item for item in items}
    assert by_name["FX-TQ-01.png"]["status"] == "已提取"
    assert by_name["坏图.png"]["status"] == "提取失败"
    assert by_name["坏图.png"]["extraction_failure_reason"]


def test_滞留在分级中或提取中的零件图启动时可回收为提取失败(
    client: TestClient, db_session: Session
) -> None:
    factory_id = create_factory(db_session, "华东精密")
    user_id = create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    grading_id = insert_part_drawing(
        db_session,
        factory_id,
        "stuck-grading.png",
        status=PartDrawingStatus.GRADING,
        uploaded_by_user_id=user_id,
    )
    extracting_id = insert_part_drawing(
        db_session,
        factory_id,
        "stuck-extracting.png",
        status=PartDrawingStatus.EXTRACTING,
        uploaded_by_user_id=user_id,
    )
    uploaded_id = insert_part_drawing(
        db_session,
        factory_id,
        "stuck-uploaded.png",
        status=PartDrawingStatus.UPLOADED,
        uploaded_by_user_id=user_id,
    )
    db_session.commit()

    recovered = RecoverStrandedPartDrawings(
        drawings=SqlInFlightPartDrawingRepository(db_session),
        events=SqlPartDrawingEventRepository(db_session),
        uow=SqlAlchemyUnitOfWork(db_session),
    ).execute()
    assert recovered == 3

    assert login(client, "quoter_a", "secret-a").status_code == 200
    for drawing_id in (grading_id, extracting_id, uploaded_id):
        body = client.get(f"/part-drawings/{drawing_id}").json()
        assert body["status"] == "提取失败"
        assert body["extraction_failure_reason"] == STRANDED_REASON
        retried = client.post(f"/part-drawings/{drawing_id}/extract")
        # 没有原图字节，重试会再次失败，但路径必须仍然开放
        assert retried.status_code == 200
        assert retried.json()["status"] == "提取失败"
