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
    "oss2",
    "pypdf",
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
    "oss2",
    "pypdf",
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


def test_对象存储端口只暴露存取签删() -> None:
    source = (SRC / "usecase" / "ports.py").read_text(encoding="utf-8")
    assert "class ObjectStorage" in source
    for name in ("def store", "def fetch", "def sign_access_url", "def delete"):
        assert name in source
    assert "oss2" not in source
    assert "aliyun" not in source.lower()


def test_用例层只依赖提取引擎抽象() -> None:
    ports = (SRC / "usecase" / "ports.py").read_text(encoding="utf-8")
    assert "class ExtractionEngine" in ports
    assert "ExtractionRequest" in ports
    assert "ExtractionResult" in ports
    extraction = (SRC / "domain" / "extraction.py").read_text(encoding="utf-8")
    assert "input_drawing_id" in extraction
    assert "quality_grade" in extraction
    upload = (SRC / "usecase" / "upload_part_drawings.py").read_text(encoding="utf-8")
    assert "ExtractionEngine" in upload
    assert "FixtureExtractionEngine" not in upload
    assert "quote_assistant.adapter.extraction" not in upload


def test_用例层不依赖框架与适配器() -> None:
    usecase_dir = SRC / "usecase"
    offenders: list[str] = []
    for path in usecase_dir.rglob("*.py"):
        source = _imported_names(path)
        for name in FORBIDDEN_IN_USECASE:
            if name in source:
                offenders.append(f"{path.relative_to(SRC)} 引用了 {name}")
    assert offenders == []
