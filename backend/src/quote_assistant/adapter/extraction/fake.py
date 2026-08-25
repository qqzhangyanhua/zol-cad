from __future__ import annotations

from quote_assistant.adapter.extraction.fixtures import raw_fixture_for
from quote_assistant.adapter.extraction.validation import parse_engine_result
from quote_assistant.domain.extraction import ExtractionRequest, ExtractionResult


class FixtureExtractionEngine:
    """Fixture-driven fake 提取引擎. Looks up presets by input-drawing id, then validates."""

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        return parse_engine_result(raw_fixture_for(request.input_drawing_id))
