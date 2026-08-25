from __future__ import annotations

import csv
import hmac
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from io import StringIO
from pathlib import Path
from uuid import UUID

from quote_assistant.domain.correction import CorrectionRecord
from quote_assistant.domain.entities import PartDrawing
from quote_assistant.domain.part_family import experimental_mark_for
from quote_assistant.domain.quote_task import QuoteTask
from quote_assistant.domain.review import fields_for_risk_labels, review_fields_for, unfinished_confirmation_items
from quote_assistant.domain.risk_labels import evaluate_risk_labels

TENANT_DELETE_CHALLENGE_TTL = timedelta(minutes=10)
TENANT_EXPORT_MEDIA_TYPE = "application/zip"
TENANT_DELETE_CONFIRMATION_INVALID_MESSAGE = "二次确认不正确或已过期，请重新发起删除"


@dataclass(frozen=True)
class TenantDeleteChallenge:
    token: str
    factory_id: UUID
    required_phrase: str
    expires_at: datetime
    created_by_user_id: UUID
    created_at: datetime
    consumed_at: datetime | None = None


@dataclass(frozen=True)
class TenantArchiveFile:
    path: str
    content: bytes


@dataclass(frozen=True)
class TenantArchive:
    filename: str
    media_type: str
    files: tuple[TenantArchiveFile, ...]


@dataclass(frozen=True)
class ExportedOriginal:
    drawing_id: UUID
    original_filename: str
    content: bytes
    missing: bool = False


def tenant_delete_confirm_phrase(factory_name: str) -> str:
    return f"删除{factory_name}的全部数据"


def new_tenant_delete_challenge(
    *,
    factory_id: UUID,
    factory_name: str,
    actor_user_id: UUID,
    token: str,
    now: datetime,
    ttl: timedelta = TENANT_DELETE_CHALLENGE_TTL,
) -> TenantDeleteChallenge:
    return TenantDeleteChallenge(
        token=token,
        factory_id=factory_id,
        required_phrase=tenant_delete_confirm_phrase(factory_name),
        expires_at=now + ttl,
        created_by_user_id=actor_user_id,
        created_at=now,
    )


def challenge_is_open(challenge: TenantDeleteChallenge, now: datetime) -> bool:
    expires_at = challenge.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return challenge.consumed_at is None and expires_at > now


def confirmation_secrets_match(expected: str, submitted: str) -> bool:
    left = expected.encode("utf-8")
    right = submitted.encode("utf-8")
    if len(left) != len(right):
        return False
    return hmac.compare_digest(left, right)


def confirmation_accepted(
    *,
    expected_token: str,
    submitted_token: str,
    expected_phrase: str,
    submitted_phrase: str,
) -> bool:
    return confirmation_secrets_match(expected_token, submitted_token) and confirmation_secrets_match(
        expected_phrase, submitted_phrase.strip()
    )


def tenant_export_filename(factory_name: str, exported_at: datetime) -> str:
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in factory_name).strip("_")
    stamp = exported_at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"本厂数据导出-{safe or 'factory'}-{stamp}.zip"


def safe_original_filename(original_filename: str) -> str:
    name = Path(original_filename).name
    if not name or name in {".", ".."}:
        return "original"
    return name


def original_archive_path(drawing_id: UUID, original_filename: str) -> str:
    return f"originals/{drawing_id}/{safe_original_filename(original_filename)}"


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def _json_bytes(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _csv_bytes(headers: tuple[str, ...], rows: Sequence[tuple[str, ...]]) -> bytes:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8-sig")


def _drawing_payload(drawing: PartDrawing, original_path: str | None) -> dict[str, object]:
    review_fields = review_fields_for(drawing)
    unfinished = unfinished_confirmation_items(drawing)
    risk_labels = evaluate_risk_labels(fields_for_risk_labels(drawing))
    return {
        "id": str(drawing.id),
        "original_filename": drawing.original_filename,
        "uploaded_at": _iso(drawing.uploaded_at),
        "content_type": drawing.content_type,
        "byte_size": drawing.byte_size,
        "page_count": drawing.page_count,
        "selected_page": drawing.selected_page,
        "status": drawing.status.value,
        "quality_grade": drawing.quality_grade.value if drawing.quality_grade else None,
        "low_quality_unreliable": drawing.low_quality_unreliable,
        "part_family_id": drawing.part_family_id,
        "experimental_mark": experimental_mark_for(drawing.part_family_id),
        "quote_task_id": str(drawing.quote_task_id) if drawing.quote_task_id else None,
        "extraction_failure_reason": drawing.extraction_failure_reason,
        "extracted_fields": [
            {
                "key": field.key,
                "label": field.label,
                "value": field.value,
                "category": field.category.value,
                "requires_confirmation": field.requires_confirmation,
                "confirmed": field.confirmed,
                "ignored": field.ignored,
                "source": field.source.value,
            }
            for field in review_fields
        ],
        "review": {
            "status": drawing.status.value,
            "pending_confirmation_count": len(unfinished),
            "pending_confirmation_labels": [field.label for field in unfinished],
        },
        "risk_labels": [
            {
                "name": label.name.value,
                "rule_id": label.rule_id,
                "triggering_value": label.triggering_value,
                "reason": label.reason,
            }
            for label in risk_labels
        ],
        "original_archive_path": original_path,
    }


def _quote_task_payload(task: QuoteTask, drawing_ids: Sequence[UUID]) -> dict[str, object]:
    return {
        "id": str(task.id),
        "name": task.name,
        "customer_name": task.customer_name,
        "created_at": _iso(task.created_at),
        "created_by_user_id": str(task.created_by_user_id),
        "part_drawing_ids": [str(drawing_id) for drawing_id in drawing_ids],
    }


def _correction_payload(record: CorrectionRecord) -> dict[str, object]:
    return {
        "id": str(record.id),
        "part_drawing_id": str(record.part_drawing_id),
        "field_key": record.field_key,
        "field_type": record.field_type,
        "old_value": record.old_value,
        "new_value": record.new_value,
        "actor_user_id": str(record.actor_user_id),
        "occurred_at": _iso(record.occurred_at),
    }


def _readme(factory_name: str) -> str:
    return (
        f"# 本厂数据导出\n\n"
        f"本压缩包是工厂「{factory_name}」的全部业务数据，可用任何 ZIP 工具打开，"
        f"也可用程序直接读取 JSON。\n\n"
        f"- `README.md`：本说明\n"
        f"- `manifest.json`：导出清单（机器可读）\n"
        f"- `part_drawings.json` / `part_drawings.csv`：零件图、提取结果、复核结果、风险标签\n"
        f"- `quote_tasks.json` / `quote_tasks.csv`：报价任务\n"
        f"- `correction_records.json` / `correction_records.csv`：修正记录\n"
        f"- `originals/`：零件图原文件，按零件图 id 分目录\n\n"
        f"JSON 是完整数据；CSV 是同一份数据的表格视图，可用表格软件打开。\n"
        f"账号与登录会话不在本包内，删除本厂数据后管理员仍可登录，只是看不到业务残留。\n"
    )


def _field_value(drawing_payload: dict[str, object], key: str) -> str:
    fields = drawing_payload.get("extracted_fields")
    if not isinstance(fields, list):
        return ""
    for item in fields:
        if isinstance(item, dict) and item.get("key") == key:
            value = item.get("value")
            return value if isinstance(value, str) else ""
    return ""


def _risk_label_names(drawing_payload: dict[str, object]) -> str:
    labels = drawing_payload.get("risk_labels")
    if not isinstance(labels, list):
        return ""
    names: list[str] = []
    for item in labels:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            names.append(str(item["name"]))
    return "、".join(names)


def build_tenant_archive(
    *,
    factory_name: str,
    exported_at: datetime,
    drawings: Sequence[PartDrawing],
    quote_tasks: Sequence[QuoteTask],
    corrections: Sequence[CorrectionRecord],
    originals: Sequence[ExportedOriginal],
) -> TenantArchive:
    originals_by_id = {item.drawing_id: item for item in originals}
    drawing_payloads: list[dict[str, object]] = []
    original_files: list[TenantArchiveFile] = []
    missing_originals: list[str] = []
    for drawing in drawings:
        original = originals_by_id.get(drawing.id)
        archive_path: str | None = None
        if original is not None and not original.missing:
            archive_path = original_archive_path(drawing.id, drawing.original_filename)
            original_files.append(TenantArchiveFile(path=archive_path, content=original.content))
        elif original is None or original.missing:
            missing_originals.append(str(drawing.id))
        drawing_payloads.append(_drawing_payload(drawing, archive_path))

    drawings_by_task: dict[UUID, list[UUID]] = {}
    for drawing in drawings:
        if drawing.quote_task_id is not None:
            drawings_by_task.setdefault(drawing.quote_task_id, []).append(drawing.id)
    task_payloads = [
        _quote_task_payload(task, drawings_by_task.get(task.id, [])) for task in quote_tasks
    ]
    correction_payloads = [_correction_payload(record) for record in corrections]
    manifest = {
        "factory_name": factory_name,
        "exported_at": _iso(exported_at),
        "format": "zip+json+csv",
        "human_readable": True,
        "counts": {
            "part_drawings": len(drawing_payloads),
            "quote_tasks": len(task_payloads),
            "correction_records": len(correction_payloads),
            "originals": len(original_files),
            "missing_originals": len(missing_originals),
        },
        "files": [
            "README.md",
            "manifest.json",
            "part_drawings.json",
            "part_drawings.csv",
            "quote_tasks.json",
            "quote_tasks.csv",
            "correction_records.json",
            "correction_records.csv",
        ],
        "missing_original_drawing_ids": missing_originals,
    }
    drawing_csv = _csv_bytes(
        (
            "id",
            "original_filename",
            "uploaded_at",
            "status",
            "quality_grade",
            "drawing_no",
            "part_name",
            "material",
            "quantity",
            "risk_labels",
            "pending_confirmation_count",
            "quote_task_id",
            "original_archive_path",
        ),
        tuple(
            (
                str(item["id"]),
                str(item["original_filename"]),
                str(item["uploaded_at"]),
                str(item["status"]),
                "" if item["quality_grade"] is None else str(item["quality_grade"]),
                _field_value(item, "drawing_no"),
                _field_value(item, "part_name"),
                _field_value(item, "material"),
                _field_value(item, "quantity"),
                _risk_label_names(item),
                str(item["review"]["pending_confirmation_count"])
                if isinstance(item["review"], dict)
                else "0",
                "" if item["quote_task_id"] is None else str(item["quote_task_id"]),
                "" if item["original_archive_path"] is None else str(item["original_archive_path"]),
            )
            for item in drawing_payloads
        ),
    )
    task_csv = _csv_bytes(
        ("id", "name", "customer_name", "created_at", "part_drawing_ids"),
        tuple(
            (
                str(item["id"]),
                str(item["name"]),
                str(item["customer_name"]),
                str(item["created_at"]),
                " ".join(str(drawing_id) for drawing_id in item["part_drawing_ids"])
                if isinstance(item["part_drawing_ids"], list)
                else "",
            )
            for item in task_payloads
        ),
    )
    correction_csv = _csv_bytes(
        (
            "id",
            "part_drawing_id",
            "field_key",
            "field_type",
            "old_value",
            "new_value",
            "actor_user_id",
            "occurred_at",
        ),
        tuple(
            (
                str(item["id"]),
                str(item["part_drawing_id"]),
                str(item["field_key"]),
                str(item["field_type"]),
                "" if item["old_value"] is None else str(item["old_value"]),
                "" if item["new_value"] is None else str(item["new_value"]),
                str(item["actor_user_id"]),
                str(item["occurred_at"]),
            )
            for item in correction_payloads
        ),
    )
    files = (
        TenantArchiveFile("README.md", _readme(factory_name).encode("utf-8")),
        TenantArchiveFile("manifest.json", _json_bytes(manifest)),
        TenantArchiveFile("part_drawings.json", _json_bytes(drawing_payloads)),
        TenantArchiveFile("part_drawings.csv", drawing_csv),
        TenantArchiveFile("quote_tasks.json", _json_bytes(task_payloads)),
        TenantArchiveFile("quote_tasks.csv", task_csv),
        TenantArchiveFile("correction_records.json", _json_bytes(correction_payloads)),
        TenantArchiveFile("correction_records.csv", correction_csv),
        *original_files,
    )
    return TenantArchive(
        filename=tenant_export_filename(factory_name, exported_at),
        media_type=TENANT_EXPORT_MEDIA_TYPE,
        files=files,
    )
