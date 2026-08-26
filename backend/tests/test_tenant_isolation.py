from __future__ import annotations

import inspect

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, insert_part_drawing, insert_quote_task, login
from quote_assistant.usecase.assign_part_drawing_to_quote_task import (
    AssignPartDrawingToQuoteTask,
    RemovePartDrawingFromQuoteTask,
)
from quote_assistant.usecase.compare_processing_time import CompareProcessingTime
from quote_assistant.usecase.continue_despite_poor_quality import ContinueDespitePoorQuality
from quote_assistant.usecase.create_quote_task import CreateQuoteTask
from quote_assistant.usecase.create_quoter import CreateQuoter
from quote_assistant.usecase.delete_tenant_data import DeleteTenantData
from quote_assistant.usecase.disable_quoter import DisableQuoter
from quote_assistant.usecase.export_quote_sheet import ExportQuoteSheet
from quote_assistant.usecase.export_tenant_data import ExportTenantData
from quote_assistant.usecase.get_factory_preferences import GetFactoryPreferences
from quote_assistant.usecase.get_part_drawing import GetPartDrawing
from quote_assistant.usecase.get_quote_task import GetQuoteTask
from quote_assistant.usecase.issue_original_access_url import IssueOriginalAccessUrl
from quote_assistant.usecase.list_correction_records import ListCorrectionRecords
from quote_assistant.usecase.list_correction_stats import ListCorrectionStats
from quote_assistant.usecase.list_factory_accounts import ListFactoryAccounts
from quote_assistant.usecase.list_factory_processing_records import ListFactoryProcessingRecords
from quote_assistant.usecase.list_part_drawing_events import ListPartDrawingEvents
from quote_assistant.usecase.list_part_drawings import ListPartDrawings
from quote_assistant.usecase.list_quote_tasks import ListQuoteTasks
from quote_assistant.usecase.list_risk_rules import ListRiskRules
from quote_assistant.usecase.process_part_drawing import ProcessPartDrawing
from quote_assistant.usecase.record_manual_baseline import RecordManualBaseline
from quote_assistant.usecase.replace_common_materials import ReplaceCommonMaterials
from quote_assistant.usecase.replace_risk_label_priority import ReplaceRiskLabelPriority
from quote_assistant.usecase.request_tenant_delete import RequestTenantDelete
from quote_assistant.usecase.review_part_drawing import (
    AddCriticalDimension,
    CompleteReview,
    ConfirmExtractedField,
    IgnoreExtractedField,
    ReopenReview,
    UnignoreExtractedField,
    UpdateExtractedField,
)
from quote_assistant.usecase.upload_part_drawings import UploadPartDrawings


def test_列出零件图用例不接受工厂标识参数() -> None:
    signature = inspect.signature(ListPartDrawings.execute)
    assert "factory_id" not in signature.parameters
    assert "tenant_id" not in signature.parameters
    assert list(signature.parameters) == ["self"]


def test_甲厂报价员读不到乙厂的零件图(client: TestClient, db_session: Session) -> None:
    factory_a = create_factory(db_session, "华东精密")
    factory_b = create_factory(db_session, "南方模具")
    create_quoter(db_session, factory_a, "quoter_a", "secret-a")
    user_b = create_quoter(db_session, factory_b, "quoter_b", "secret-b")
    drawing_b = insert_part_drawing(
        db_session, factory_b, "乙厂-轴套.pdf", uploaded_by_user_id=user_b
    )
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
    user_b = create_quoter(db_session, factory_b, "quoter_b", "secret-b")
    insert_part_drawing(db_session, factory_b, "乙厂-法兰.pdf", uploaded_by_user_id=user_b)
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
        ProcessPartDrawing,
        ListPartDrawingEvents,
        ConfirmExtractedField,
        UpdateExtractedField,
        IgnoreExtractedField,
        UnignoreExtractedField,
        AddCriticalDimension,
        ReopenReview,
        CompleteReview,
        ListCorrectionRecords,
        ListCorrectionStats,
        CompareProcessingTime,
        RecordManualBaseline,
        CreateQuoteTask,
        ListQuoteTasks,
        GetQuoteTask,
        AssignPartDrawingToQuoteTask,
        RemovePartDrawingFromQuoteTask,
        ExportQuoteSheet,
        CreateQuoter,
        DisableQuoter,
        ListFactoryAccounts,
        ListFactoryProcessingRecords,
        GetFactoryPreferences,
        ReplaceCommonMaterials,
        ReplaceRiskLabelPriority,
        ListRiskRules,
        ExportTenantData,
        RequestTenantDelete,
        DeleteTenantData,
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
    assert client.post(f"/part-drawings/{drawing_id}/fields/drawing_no/ignore").status_code == 404
    assert client.post(f"/part-drawings/{drawing_id}/fields/drawing_no/unignore").status_code == 404
    assert (
        client.post(
            f"/part-drawings/{drawing_id}/fields",
            json={"kind": "deepest_hole", "value": "Ø8×48"},
        ).status_code
        == 404
    )
    assert client.post(f"/part-drawings/{drawing_id}/reopen-review").status_code == 404
    assert client.get(f"/part-drawings/{drawing_id}/correction-records").status_code == 404
    assert client.get("/quote-tasks").json() == {"items": []}
    assert client.get(f"/quote-tasks/{drawing_id}").status_code == 404
    assert (
        client.post(
            f"/quote-tasks/{drawing_id}/part-drawings",
            json={"part_drawing_id": drawing_id},
        ).status_code
        == 404
    )


def test_甲厂报价员看不到乙厂的报价任务也不能归入乙厂零件图(
    client: TestClient, db_session: Session
) -> None:
    factory_a = create_factory(db_session, "华东精密")
    factory_b = create_factory(db_session, "南方模具")
    create_quoter(db_session, factory_a, "quoter_a", "secret-a")
    user_b = create_quoter(db_session, factory_b, "quoter_b", "secret-b")
    drawing_b = insert_part_drawing(
        db_session, factory_b, "乙厂-轴套.pdf", uploaded_by_user_id=user_b
    )
    task_b = insert_quote_task(db_session, factory_b, "乙厂询价", "乙厂客户", user_b)
    db_session.commit()

    assert login(client, "quoter_a", "secret-a").status_code == 200
    listed = client.get("/quote-tasks", params={"factory_id": str(factory_b)})
    assert listed.status_code == 200
    assert listed.json() == {"items": []}
    assert client.get(f"/quote-tasks/{task_b}").status_code == 404
    assert client.get(f"/quote-tasks/{task_b}/quote-sheet").status_code == 404
    assert (
        client.post(
            f"/quote-tasks/{task_b}/part-drawings",
            json={"part_drawing_id": str(drawing_b)},
        ).status_code
        == 404
    )
    assert client.delete(f"/quote-tasks/{task_b}/part-drawings/{drawing_b}").status_code == 404

    created = client.post("/quote-tasks", json={"name": "甲厂任务", "customer_name": "甲厂客户"})
    assert created.status_code == 200
    assert (
        client.post(
            f"/quote-tasks/{created.json()['id']}/part-drawings",
            json={"part_drawing_id": str(drawing_b)},
        ).status_code
        == 404
    )
