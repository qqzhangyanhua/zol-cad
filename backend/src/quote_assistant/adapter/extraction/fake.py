from __future__ import annotations

from quote_assistant.adapter.extraction.fixtures import FIXTURE_RESULTS, resolve_fixture_key
from quote_assistant.domain.extraction import ExtractionRequest, ExtractionResult


class FixtureExtractionEngine:
    """Fixture-driven fake 提取引擎. Looks up presets by input-drawing id."""

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        key = resolve_fixture_key(request.input_drawing_id)
        return FIXTURE_RESULTS[key]
