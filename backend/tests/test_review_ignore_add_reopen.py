from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from drawing_fixtures import PNG_1X1
from helpers import create_factory, create_quoter, login
from quote_assistant.domain.extraction import (
    ExtractedField,
    ExtractionRequest,
    ExtractionResult,
    FieldCategory,
)
from quote_assistant.domain.quality import QualityGrade

HIGH_RISK_KEYS = ("tightest_tolerance", "max_envelope", "deepest_hole", "thinnest_wall")


def _upload(client: TestClient, filename: str) -> dict:
    response = client.post(
        "/part-drawings",
        files=[("files", (filename, PNG_1X1, "image/png"))],
    )
    assert response.status_code == 200
    return response.json()["items"][0]


def _login_quoter(client: TestClient, db_session: Session) -> None:
    factory_id = create_factory(db_session, "华东精密")
    create_quoter(db_session, factory_id, "quoter_a", "secret-a")
    db_session.commit()
    assert login(client, "quoter_a", "secret-a").status_code == 200


def _fields_by_key(item: dict) -> dict[str, dict]:
    return {field["key"]: field for field in item["extracted_fields"]}


def _confirm(client: TestClient, drawing_id: str, field_key: str):
    return client.post(f"/part-drawings/{drawing_id}/fields/{field_key}/confirm")


def _ignore(client: TestClient, drawing_id: str, field_key: str):
    return client.post(f"/part-drawings/{drawing_id}/fields/{field_key}/ignore")


def _unignore(client: TestClient, drawing_id: str, field_key: str):
    return client.post(f"/part-drawings/{drawing_id}/fields/{field_key}/unignore")


def _complete(client: TestClient, drawing_id: str):
    return client.post(f"/part-drawings/{drawing_id}/complete-review")


def _reopen(client: TestClient, drawing_id: str):
    return client.post(f"/part-drawings/{drawing_id}/reopen-review")


def _label_names(item: dict) -> set[str]:
    return {label["name"] for label in item["risk_labels"]}


class _OverwriteEngine:
    """Returns different values so seam 1 can prove retry does not wipe edits."""

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        del request
        return ExtractionResult(
            quality_grade=QualityGrade.CLEAR,
            is_assembly_or_exploded=False,
            fields=(
                ExtractedField("drawing_no", "图号", "NEW-999", FieldCategory.TITLE_BLOCK),
                ExtractedField("part_name", "零件名称", "被覆盖件", FieldCategory.TITLE_BLOCK),
                ExtractedField("material", "材料", "Q235", FieldCategory.TITLE_BLOCK),
                ExtractedField("quantity", "数量", "9", FieldCategory.TITLE_BLOCK),
                ExtractedField(
                    "tightest_tolerance", "最严公差", "IT8", FieldCategory.CRITICAL_DIMENSION
                ),
                ExtractedField("max_envelope", "最大外形", "Ø1×1", FieldCategory.CRITICAL_DIMENSION),
                ExtractedField("deepest_hole", "最深孔", "Ø1×1", FieldCategory.CRITICAL_DIMENSION),
                ExtractedField("thinnest_wall", "最薄壁", "9", FieldCategory.CRITICAL_DIMENSION),
            ),
        )


def test_忽略项不阻塞已复核且仍可见可撤销(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TQ-01.png")
    drawing_id = item["id"]

    ignored = _ignore(client, drawing_id, "thinnest_wall")
    assert ignored.status_code == 200
    field = _fields_by_key(ignored.json())["thinnest_wall"]
    assert field["ignored"] is True
    assert field["value"] is None
    assert "最薄壁" not in ignored.json()["pending_confirmation_labels"]
    assert ignored.json()["pending_confirmation_count"] == 3

    for key in ("tightest_tolerance", "max_envelope", "deepest_hole"):
        assert _confirm(client, drawing_id, key).status_code == 200

    done = _complete(client, drawing_id)
    assert done.status_code == 200
    assert done.json()["status"] == "已复核"
    still_there = _fields_by_key(done.json())["thinnest_wall"]
    assert still_there["ignored"] is True
    assert still_there["label"] == "最薄壁"

    assert _unignore(client, drawing_id, "thinnest_wall").status_code == 409

    reopened = _reopen(client, drawing_id)
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "复核中"
    assert _fields_by_key(reopened.json())["thinnest_wall"]["ignored"] is True

    restored = _unignore(client, drawing_id, "thinnest_wall")
    assert restored.status_code == 200
    restored_field = _fields_by_key(restored.json())["thinnest_wall"]
    assert restored_field["ignored"] is False
    assert "最薄壁" in restored.json()["pending_confirmation_labels"]

    blocked = _complete(client, drawing_id)
    assert blocked.status_code == 409
    assert "最薄壁" in blocked.json()["detail"]
    assert client.get(f"/part-drawings/{drawing_id}").json()["status"] == "复核中"


def test_补录关键尺寸进入结果并参与风险标签(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TQ-01.png")
    drawing_id = item["id"]
    assert _label_names(item) == set()
    assert _fields_by_key(item)["deepest_hole"]["value"] is None

    added = client.post(
        f"/part-drawings/{drawing_id}/fields",
        json={"kind": "deepest_hole", "value": "Ø8×48"},
    )
    assert added.status_code == 200
    body = added.json()
    field = _fields_by_key(body)["deepest_hole"]
    assert field["value"] == "Ø8×48"
    assert field["source"] == "added"
    assert field["confirmed"] is True
    assert field["category"] == "关键尺寸"
    assert "深孔" in _label_names(body)

    extra = client.post(
        f"/part-drawings/{drawing_id}/fields",
        json={"kind": "tightest_tolerance", "value": "IT6", "label": "另一处严公差"},
    )
    assert extra.status_code == 200
    extra_body = extra.json()
    extra_field = _fields_by_key(extra_body)["tightest_tolerance__added__1"]
    assert extra_field["value"] == "IT6"
    assert extra_field["label"] == "另一处严公差"
    assert extra_field["source"] == "added"
    assert extra_field["category"] == "关键尺寸"
    assert extra_field["confirmed"] is True
    assert "高精度" in _label_names(extra_body)
    assert any(field["key"] == "tightest_tolerance__added__1" for field in extra_body["extracted_fields"])


def test_修正关键尺寸后风险标签按确认值重算(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "WIRE-RL-01.png")
    drawing_id = item["id"]
    assert "高精度" in _label_names(item)
    assert "薄壁" in _label_names(item)

    loosened = client.patch(
        f"/part-drawings/{drawing_id}/fields/tightest_tolerance",
        json={"value": "IT8"},
    )
    assert loosened.status_code == 200
    loosened_body = loosened.json()
    assert _fields_by_key(loosened_body)["tightest_tolerance"]["value"] == "IT8"
    assert _fields_by_key(loosened_body)["tightest_tolerance"]["confirmed"] is True
    assert "高精度" not in _label_names(loosened_body)
    assert "薄壁" in _label_names(loosened_body)

    reread = client.get(f"/part-drawings/{drawing_id}").json()
    assert _fields_by_key(reread)["tightest_tolerance"]["value"] == "IT8"
    assert "高精度" not in _label_names(reread)

    tightened = client.patch(
        f"/part-drawings/{drawing_id}/fields/tightest_tolerance",
        json={"value": "IT5"},
    )
    assert tightened.status_code == 200
    assert "高精度" in _label_names(tightened.json())
    assert tightened.json()["risk_labels"][0]["triggering_value"] == "IT5"

    ignored = _ignore(client, drawing_id, "thinnest_wall")
    assert ignored.status_code == 200
    assert "薄壁" not in _label_names(ignored.json())


def test_已复核可重开修改且再标记仍需无未处理需确认项(
    client: TestClient, db_session: Session
) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TQ-01.png")
    drawing_id = item["id"]
    for key in HIGH_RISK_KEYS:
        assert _confirm(client, drawing_id, key).status_code == 200
    assert _complete(client, drawing_id).json()["status"] == "已复核"

    blocked_edit = client.patch(
        f"/part-drawings/{drawing_id}/fields/tightest_tolerance",
        json={"value": "IT6"},
    )
    assert blocked_edit.status_code == 409
    assert "重新打开" in blocked_edit.json()["detail"]

    reopened = _reopen(client, drawing_id)
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "复核中"
    assert _fields_by_key(reopened.json())["tightest_tolerance"]["confirmed"] is True

    edited = client.patch(
        f"/part-drawings/{drawing_id}/fields/tightest_tolerance",
        json={"value": "IT6"},
    )
    assert edited.status_code == 200
    assert edited.json()["status"] == "复核中"
    assert _fields_by_key(edited.json())["tightest_tolerance"]["value"] == "IT6"
    assert "高精度" in _label_names(edited.json())

    refreshed = client.get(f"/part-drawings/{drawing_id}").json()
    assert refreshed["status"] == "复核中"
    assert _fields_by_key(refreshed)["tightest_tolerance"]["value"] == "IT6"
    assert refreshed["pending_confirmation_count"] == 0

    again = _complete(client, drawing_id)
    assert again.status_code == 200
    assert again.json()["status"] == "已复核"
    assert _fields_by_key(again.json())["tightest_tolerance"]["value"] == "IT6"


def test_重开后撤销忽略使需确认重新挡住已复核(client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TQ-01.png")
    drawing_id = item["id"]
    assert _ignore(client, drawing_id, "thinnest_wall").status_code == 200
    for key in ("tightest_tolerance", "max_envelope", "deepest_hole"):
        assert _confirm(client, drawing_id, key).status_code == 200
    assert _complete(client, drawing_id).json()["status"] == "已复核"

    assert _reopen(client, drawing_id).status_code == 200
    restored = _unignore(client, drawing_id, "thinnest_wall")
    assert restored.status_code == 200
    assert restored.json()["pending_confirmation_count"] == 1
    blocked = _complete(client, drawing_id)
    assert blocked.status_code == 409
    assert "最薄壁" in blocked.json()["detail"]


def test_重试提取不冲掉已有复核修改(app, client: TestClient, db_session: Session) -> None:
    _login_quoter(client, db_session)
    item = _upload(client, "FX-TQ-01.png")
    drawing_id = item["id"]
    assert _fields_by_key(item)["drawing_no"]["value"] == "FL-001"
    assert _fields_by_key(item)["tightest_tolerance"]["value"] == "IT7"

    patched = client.patch(
        f"/part-drawings/{drawing_id}/fields/tightest_tolerance",
        json={"value": "IT6"},
    )
    assert patched.status_code == 200
    assert _ignore(client, drawing_id, "thinnest_wall").status_code == 200
    added = client.post(
        f"/part-drawings/{drawing_id}/fields",
        json={"kind": "deepest_hole", "value": "Ø8×48"},
    )
    assert added.status_code == 200

    app.state.extraction_engine = _OverwriteEngine()
    retried = client.post(f"/part-drawings/{drawing_id}/extract")
    assert retried.status_code == 200
    body = retried.json()
    assert body["status"] == "已提取"
    fields = _fields_by_key(body)
    assert fields["tightest_tolerance"]["value"] == "IT6"
    assert fields["tightest_tolerance"]["confirmed"] is True
    assert fields["thinnest_wall"]["ignored"] is True
    assert fields["thinnest_wall"]["value"] is None
    assert fields["deepest_hole"]["value"] == "Ø8×48"
    assert fields["deepest_hole"]["source"] == "added"
    assert fields["drawing_no"]["value"] == "NEW-999"
    assert fields["part_name"]["value"] == "被覆盖件"
    assert "高精度" in _label_names(body)
    assert "深孔" in _label_names(body)

    reread = client.get(f"/part-drawings/{drawing_id}").json()
    reread_fields = _fields_by_key(reread)
    assert reread_fields["tightest_tolerance"]["value"] == "IT6"
    assert reread_fields["thinnest_wall"]["ignored"] is True
    assert reread_fields["deepest_hole"]["value"] == "Ø8×48"
    assert reread_fields["drawing_no"]["value"] == "NEW-999"
