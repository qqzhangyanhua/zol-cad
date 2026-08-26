"""Onboarding CLI for a factory 报价底稿 template.

This is a team tool, not a product feature. There is no HTTP write path and
the 管理员 settings page must not grow a mapping UI.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from quote_assistant.adapter.db.models import FactoryRow
from quote_assistant.adapter.db.repositories import SqlQuoteSheetTemplateRepository
from quote_assistant.adapter.db.session import (
    SqlAlchemyUnitOfWork,
    make_engine,
    make_session_factory,
)
from quote_assistant.config import Settings
from quote_assistant.domain.entities import Actor, Role
from quote_assistant.domain.errors import InvalidQuoteSheetTemplate
from quote_assistant.domain.quote_sheet import (
    QUOTE_SHEET_SOURCE_KEYS,
    QuoteSheetTemplate,
    resolve_quote_sheet_template,
)
from quote_assistant.usecase.save_quote_sheet_template import (
    GetQuoteSheetTemplate,
    SaveQuoteSheetTemplate,
)

_ONBOARDING_USERNAME = "onboarding-cli"


def main(argv: Sequence[str] | None = None, *, database_url: str | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    url = database_url or Settings().database_url
    try:
        if args.command == "show":
            _run_show(url, args)
        else:
            _run_save(url, args)
    except InvalidQuoteSheetTemplate as exc:
        print(f"模板不合法：{exc}", file=sys.stderr)
        return 1
    except CliError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


class CliError(Exception):
    """Factory lookup or file-format failure in the onboarding tool."""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m quote_assistant.interface.cli.quote_sheet_template",
        description=(
            "为指定工厂写入 / 更新 / 查看报价底稿列模板。"
            "这是团队 onboarding 工具，不是产品功能，也不走 HTTP。"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="查看该工厂已写入的模板，没有则显示默认列")
    _add_factory_args(show)
    show.add_argument("--json", action="store_true", help="以 JSON 输出，便于脚本读取")

    save = sub.add_parser("save", help="写入或更新该工厂的模板（走领域校验）")
    _add_factory_args(save)
    save.add_argument(
        "--columns-file",
        type=Path,
        help='JSON 数组，每项 {"source_key": "...", "header": "..."}',
    )
    save.add_argument(
        "--column",
        action="append",
        default=[],
        metavar="SOURCE_KEY:HEADER",
        help="重复传入以逐列指定，例如 --column part_name:品名",
    )
    return parser


def _add_factory_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--factory-name", help="工厂名称（重名时请改用 --factory-id）")
    group.add_argument("--factory-id", type=UUID, help="工厂 UUID")


def _run_show(database_url: str, args: argparse.Namespace) -> None:
    with _session_scope(database_url) as session:
        factory = _load_factory(
            session, factory_id=args.factory_id, factory_name=args.factory_name
        )
        actor = _onboarding_actor(factory)
        stored = GetQuoteSheetTemplate(
            actor, SqlQuoteSheetTemplateRepository(session)
        ).execute()
        resolved = resolve_quote_sheet_template(stored)
        if args.json:
            print(json.dumps(_show_payload(factory, stored, resolved), ensure_ascii=False, indent=2))
            return
        _print_show(factory, stored, resolved)


def _run_save(database_url: str, args: argparse.Namespace) -> None:
    raw_columns = _load_raw_columns(args)
    with _session_scope(database_url) as session:
        factory = _load_factory(
            session, factory_id=args.factory_id, factory_name=args.factory_name
        )
        actor = _onboarding_actor(factory)
        resolved = SaveQuoteSheetTemplate(
            actor,
            SqlQuoteSheetTemplateRepository(session),
            SqlAlchemyUnitOfWork(session),
        ).execute(raw_columns)
        print(f"已写入工厂「{factory.name}」({factory.id}) 的报价底稿模板，导出将使用以下列：")
        _print_columns(resolved)


@contextmanager
def _session_scope(database_url: str) -> Iterator[Session]:
    engine = make_engine(database_url)
    session = make_session_factory(engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _onboarding_actor(factory: FactoryRow) -> Actor:
    return Actor(
        user_id=factory.id,
        factory_id=factory.id,
        factory_name=factory.name,
        username=_ONBOARDING_USERNAME,
        role=Role.ADMIN,
    )


def _load_factory(
    session: Session,
    *,
    factory_id: UUID | None,
    factory_name: str | None,
) -> FactoryRow:
    if factory_id is not None:
        row = session.get(FactoryRow, factory_id)
        if row is None:
            raise CliError(f"找不到工厂：{factory_id}")
        return row
    assert factory_name is not None
    rows = list(
        session.execute(select(FactoryRow).where(FactoryRow.name == factory_name)).scalars()
    )
    if not rows:
        raise CliError(f"找不到工厂：{factory_name}")
    if len(rows) > 1:
        ids = "、".join(str(row.id) for row in rows)
        raise CliError(f"工厂名称重复，请改用 --factory-id：{ids}")
    return rows[0]


def _load_raw_columns(args: argparse.Namespace) -> list[object]:
    from_file = _load_columns_file(args.columns_file) if args.columns_file is not None else []
    from_flags = [_parse_column_flag(item) for item in args.column]
    combined = from_file + from_flags
    if not combined:
        raise CliError("请用 --columns-file 或 --column 提供至少一列")
    return combined


def _load_columns_file(path: Path) -> list[object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CliError(f"无法读取模板文件：{exc}") from exc
    if not isinstance(payload, list):
        raise CliError("模板文件必须是列对象数组")
    return payload


def _parse_column_flag(raw: str) -> dict[str, str]:
    if ":" not in raw:
        raise CliError(f"--column 格式应为 source_key:标题，收到：{raw}")
    source_key, header = raw.split(":", 1)
    return {"source_key": source_key.strip(), "header": header.strip()}


def _show_payload(
    factory: FactoryRow,
    stored: QuoteSheetTemplate | None,
    resolved: QuoteSheetTemplate,
) -> dict[str, object]:
    return {
        "factory_id": str(factory.id),
        "factory_name": factory.name,
        "stored": stored is not None,
        "stored_columns": _columns_payload(stored) if stored is not None else [],
        "resolved_columns": _columns_payload(resolved),
        "available_source_keys": sorted(QUOTE_SHEET_SOURCE_KEYS),
        "team_tool": True,
    }


def _columns_payload(template: QuoteSheetTemplate) -> list[dict[str, str]]:
    return [
        {"source_key": column.source_key, "header": column.header} for column in template.columns
    ]


def _print_show(
    factory: FactoryRow,
    stored: QuoteSheetTemplate | None,
    resolved: QuoteSheetTemplate,
) -> None:
    print("报价底稿模板 — 团队 onboarding 工具（不是产品功能）")
    print(f"工厂：{factory.name} ({factory.id})")
    if stored is None:
        print("已写入：否（导出使用默认列）")
    else:
        print("已写入：是")
        print("已存列：")
        _print_columns(stored)
    print("导出将使用：")
    _print_columns(resolved)
    print("可用源字段：" + "、".join(sorted(QUOTE_SHEET_SOURCE_KEYS)))


def _print_columns(template: QuoteSheetTemplate) -> None:
    for index, column in enumerate(template.columns, start=1):
        print(f"  {index}. {column.source_key} → {column.header}")


if __name__ == "__main__":
    raise SystemExit(main())
