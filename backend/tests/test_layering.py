from __future__ import annotations

from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "quote_assistant"

FORBIDDEN_IN_DOMAIN = (
    "fastapi",
    "sqlalchemy",
    "alembic",
    "httpx",
    "psycopg",
    "starlette",
    "pwdlib",
    "quote_assistant.adapter",
    "quote_assistant.interface",
)

FORBIDDEN_IN_USECASE = (
    "fastapi",
    "sqlalchemy",
    "alembic",
    "httpx",
    "psycopg",
    "starlette",
    "pwdlib",
    "quote_assistant.adapter",
    "quote_assistant.interface",
)


def _imported_names(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_领域层不依赖外部IO() -> None:
    domain_dir = SRC / "domain"
    offenders: list[str] = []
    for path in domain_dir.rglob("*.py"):
        source = _imported_names(path)
        for name in FORBIDDEN_IN_DOMAIN:
            if name in source:
                offenders.append(f"{path.relative_to(SRC)} 引用了 {name}")
    assert offenders == []


def test_用例层不依赖框架与适配器() -> None:
    usecase_dir = SRC / "usecase"
    offenders: list[str] = []
    for path in usecase_dir.rglob("*.py"):
        source = _imported_names(path)
        for name in FORBIDDEN_IN_USECASE:
            if name in source:
                offenders.append(f"{path.relative_to(SRC)} 引用了 {name}")
    assert offenders == []
