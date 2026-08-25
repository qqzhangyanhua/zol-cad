from __future__ import annotations

from quote_assistant.adapter.extraction.cost import InMemoryExtractionCostCounter
from quote_assistant.adapter.extraction.fake import FixtureExtractionEngine
from quote_assistant.adapter.extraction.vendor import (
    UnconfiguredVendorTransport,
    VendorExtractionEngine,
)
from quote_assistant.config import Settings

ENGINE_FIXTURE = "fixture"
ENGINE_VENDOR = "vendor"


def normalize_extraction_engine(value: str) -> str:
    kind = value.strip().lower()
    if kind in {ENGINE_FIXTURE, ENGINE_VENDOR}:
        return kind
    raise ValueError(f"未知提取引擎开关：{value}（允许 fixture / vendor）")


def build_extraction_engine(
    settings: Settings,
) -> FixtureExtractionEngine | VendorExtractionEngine:
    """Default stays fixture so seam-1 keeps the fake engine. vendor is the unpaid skeleton."""
    kind = normalize_extraction_engine(settings.extraction_engine)
    if kind == ENGINE_VENDOR:
        return VendorExtractionEngine(
            transport=UnconfiguredVendorTransport(),
            cost_recorder=InMemoryExtractionCostCounter(),
        )
    return FixtureExtractionEngine()
