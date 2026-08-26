from __future__ import annotations

from quote_assistant.adapter.extraction.fixtures import raw_fixture_for
from quote_assistant.adapter.extraction.validation import parse_engine_result
from quote_assistant.config import FIXTURE_ENGINE_FORBIDDEN_MESSAGE, FixtureEngineNotAllowed
from quote_assistant.domain.extraction import ExtractionRequest, ExtractionResult
from quote_assistant.domain.prompt_templates import prompt_template_for


class FixtureExtractionEngine:
    """Fixture-driven fake 提取引擎. Looks up presets by input-drawing id, then validates.

    Direct construction defaults to allowed so seam-1 tests can swap it onto app.state.
    Production must not construct or call this — factory refuses to select it.
    """

    def __init__(self, *, allowed: bool = True) -> None:
        if not allowed:
            raise FixtureEngineNotAllowed(FIXTURE_ENGINE_FORBIDDEN_MESSAGE)
        self._allowed = allowed
        self.last_prompt_template_id: str | None = None

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        if not self._allowed:
            raise FixtureEngineNotAllowed(FIXTURE_ENGINE_FORBIDDEN_MESSAGE)
        template = prompt_template_for(request.part_family_id)
        self.last_prompt_template_id = template.id
        return parse_engine_result(raw_fixture_for(request.input_drawing_id))
