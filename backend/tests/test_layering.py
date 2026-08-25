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
    "openpyxl",
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
    "openpyxl",
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
    assert "part_family_id" in extraction
    assert "quality_grade" in extraction
    prompts = (SRC / "domain" / "prompt_templates.py").read_text(encoding="utf-8")
    assert "def prompt_template_for" in prompts
    upload = (SRC / "usecase" / "upload_part_drawings.py").read_text(encoding="utf-8")
    extract = (SRC / "usecase" / "extract_part_drawing.py").read_text(encoding="utf-8")
    assert "ExtractionEngine" in upload
    assert "ExtractionEngine" in extract
    assert "part_family_id" in upload
    assert "part_family_id" in extract
    assert "FixtureExtractionEngine" not in upload
    assert "FixtureExtractionEngine" not in extract
    assert "VendorExtractionEngine" not in upload
    assert "VendorExtractionEngine" not in extract
    assert "quote_assistant.adapter.extraction" not in upload
    assert "quote_assistant.adapter.extraction" not in extract
    factory = (SRC / "adapter" / "extraction" / "factory.py").read_text(encoding="utf-8")
    assert "ENGINE_FIXTURE" in factory
    assert "def build_extraction_engine" in factory
    assert "prompt_template_for" not in upload
    assert "prompt_template_for" not in extract
    assert "【专用模板" not in upload
    assert "【专用模板" not in extract
    assert "【通用模板" not in upload
    assert "【通用模板" not in extract


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


def test_报价底稿导出规则在领域层且管理员界面没有字段映射() -> None:
    quote_sheet = (SRC / "domain" / "quote_sheet.py").read_text(encoding="utf-8")
    assert "def build_quote_sheet_table" in quote_sheet
    assert "def unreviewed_drawings_for_export" in quote_sheet
    assert "REQUIRED_QUOTE_SHEET_SOURCE_KEYS" in quote_sheet
    assert "risk_labels" in quote_sheet
    assert "experimental_mark" in quote_sheet
    assert "low_quality_mark" in quote_sheet
    export_use_case = (SRC / "usecase" / "export_quote_sheet.py").read_text(encoding="utf-8")
    assert "openpyxl" not in export_use_case
    assert "evaluate_risk_labels" not in export_use_case
    http_src = "".join(path.read_text(encoding="utf-8") for path in (SRC / "interface" / "http").rglob("*.py"))
    assert "quote-sheet-templates" not in http_src
    assert "class QuoteSheetTemplateRequest" not in http_src

    frontend = SRC.parents[2] / "frontend" / "src"
    offenders: list[str] = []
    needles = ("字段映射", "导出模板", "source_key", "quote-sheet-template", "QuoteSheetTemplate")
    for path in list(frontend.rglob("*.ts")) + list(frontend.rglob("*.tsx")):
        source = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle in source:
                offenders.append(f"{path.relative_to(frontend)} 含有 {needle}")
    assert offenders == []


def test_报价任务归集逻辑在领域层且不含金额审批字段() -> None:
    quote_task = (SRC / "domain" / "quote_task.py").read_text(encoding="utf-8")
    assert "def derive_quote_task_review_status" in quote_task
    assert "def new_quote_task" in quote_task
    assert "class QuoteTask" in quote_task
    assert "class QuoteTaskReviewStatus" in quote_task
    schemas = (SRC / "interface" / "http" / "schemas.py").read_text(encoding="utf-8")
    assert "class CreateQuoteTaskRequest" in schemas
    assert "class QuoteTaskDetailResponse" in schemas
    assert "amount" not in schemas
    assert "price" not in schemas
    assert "approval" not in schemas
    for path in (SRC / "usecase").glob("*quote_task*.py"):
        source = path.read_text(encoding="utf-8")
        assert "amount" not in source
        assert "price" not in source
        assert "approval" not in source


def test_本厂数据导出打包在适配器_确认短语在领域层() -> None:
    tenant_data = (SRC / "domain" / "tenant_data.py").read_text(encoding="utf-8")
    assert "def tenant_delete_confirm_phrase" in tenant_data
    assert "def confirmation_accepted" in tenant_data
    assert "def build_tenant_archive" in tenant_data
    assert "zipfile" not in tenant_data
    export_use_case = (SRC / "usecase" / "export_tenant_data.py").read_text(encoding="utf-8")
    delete_use_case = (SRC / "usecase" / "delete_tenant_data.py").read_text(encoding="utf-8")
    assert "zipfile" not in export_use_case
    assert "zipfile" not in delete_use_case
    assert "evaluate_risk_labels" not in export_use_case
    writer = (SRC / "adapter" / "export" / "tenant_archive_writer.py").read_text(encoding="utf-8")
    assert "zipfile" in writer


def test_保密说明用例只读端口且不写承诺() -> None:
    notice = (SRC / "usecase" / "get_confidentiality_notice.py").read_text(encoding="utf-8")
    ports = (SRC / "usecase" / "ports.py").read_text(encoding="utf-8")
    domain = (SRC / "domain" / "confidentiality.py").read_text(encoding="utf-8")
    assert "class GetConfidentialityNotice" in notice
    assert "ConfidentialityPolicySource" in notice
    assert "quote_assistant.adapter" not in notice
    assert "class ConfidentialityPolicySource" in ports
    assert "class ConfidentialityNotice" in domain
    frontend = SRC.parents[2] / "frontend" / "src"
    offenders: list[str] = []
    forbidden = ("已签署 DPA", "数据保证在中国大陆", "承诺不用于训练")
    for path in list(frontend.rglob("*.ts")) + list(frontend.rglob("*.tsx")):
        source = path.read_text(encoding="utf-8")
        for needle in forbidden:
            if needle in source:
                offenders.append(f"{path.relative_to(frontend)} 含有 {needle}")
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
