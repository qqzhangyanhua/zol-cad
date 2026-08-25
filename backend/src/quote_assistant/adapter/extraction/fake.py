from __future__ import annotations

from quote_assistant.adapter.extraction.fixtures import raw_fixture_for
from quote_assistant.adapter.extraction.validation import parse_engine_result
from quote_assistant.domain.extraction import ExtractionRequest, ExtractionResult
from quote_assistant.domain.prompt_templates import prompt_template_for


class FixtureExtractionEngine:
    """Fixture-driven fake 提取引擎. Looks up presets by input-drawing id, then validates."""

    def __init__(self) -> None:
        self.last_prompt_template_id: str | None = None

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        template = prompt_template_for(request.part_family_id)
        self.last_prompt_template_id = template.id
        return parse_engine_result(raw_fixture_for(request.input_drawing_id))
