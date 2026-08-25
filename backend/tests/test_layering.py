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
    extract = (SRC / "usecase" / "extract_part_drawing.py").read_text(encoding="utf-8")
    assert "ExtractionEngine" in upload
    assert "ExtractionEngine" in extract
    assert "FixtureExtractionEngine" not in upload
    assert "FixtureExtractionEngine" not in extract
    assert "quote_assistant.adapter.extraction" not in upload
    assert "quote_assistant.adapter.extraction" not in extract


def test_高风险字段判定表只活在领域层() -> None:
    review = (SRC / "domain" / "review.py").read_text(encoding="utf-8")
    assert "HIGH_RISK_FIELD_CLASSES" in review
    assert "FIELD_RISK_CLASS_BY_KEY" in review
    assert "def field_requires_confirmation" in review
    assert "尺寸类" in review
    assert "公差类" in review

    schemas = (SRC / "interface" / "http" / "schemas.py").read_text(encoding="utf-8")
    assert "review_fields_for" in schemas
    assert "FIELD_RISK_CLASS_BY_KEY" not in schemas

    for path in (SRC / "usecase").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "HIGH_RISK_FIELD_CLASSES" not in source
        assert "FIELD_RISK_CLASS_BY_KEY" not in source
        assert "尺寸类" not in source
        assert "公差类" not in source

    frontend = SRC.parents[2] / "frontend" / "src"
    offenders: list[str] = []
    for path in list(frontend.rglob("*.ts")) + list(frontend.rglob("*.tsx")):
        source = path.read_text(encoding="utf-8")
        if "HIGH_RISK_FIELD" in source or "FIELD_RISK_CLASS" in source:
            offenders.append(str(path.relative_to(frontend)))
        if "field_requires_confirmation" in source:
            offenders.append(str(path.relative_to(frontend)))
        if "quality_grade === \"清晰\"" in source or "quality_grade === '清晰'" in source:
            offenders.append(f"{path.relative_to(frontend)} 用图纸质量分级自行判断需确认")
    assert offenders == []


def test_风险规则引擎在领域层且用例不自行判断() -> None:
    risk = (SRC / "domain" / "risk_labels.py").read_text(encoding="utf-8")
    assert "def evaluate_risk_labels" in risk
    assert "class RiskLabel" in risk
    assert "FORBIDDEN_RISK_LABEL_SEMANTICS" in risk
    schemas = (SRC / "interface" / "http" / "schemas.py").read_text(encoding="utf-8")
    assert "evaluate_risk_labels" in schemas
    for path in (SRC / "usecase").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "高精度" not in source
        assert "evaluate_risk_labels" not in source


def test_用例层不依赖框架与适配器() -> None:
    usecase_dir = SRC / "usecase"
    offenders: list[str] = []
    for path in usecase_dir.rglob("*.py"):
        source = _imported_names(path)
        for name in FORBIDDEN_IN_USECASE:
            if name in source:
                offenders.append(f"{path.relative_to(SRC)} 引用了 {name}")
    assert offenders == []
