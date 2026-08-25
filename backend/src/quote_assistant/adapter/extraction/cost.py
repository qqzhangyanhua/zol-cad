from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ExtractionCostEvent:
    """Per-call cost accounting. Never includes image bytes or file content."""

    input_drawing_id: str
    page_byte_size: int
    prompt_template_id: str
    outcome: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    estimated_cost: float | None = None


class ExtractionCostRecorder(Protocol):
    def record(self, event: ExtractionCostEvent) -> None:
        """Record one 读图取数 call. Implementations must not store image bytes."""


@dataclass
class InMemoryExtractionCostCounter:
    """No-op-until-vendor counter. A trial can swap this for a billed meter later."""

    total_calls: int = 0
    events: list[ExtractionCostEvent] = field(default_factory=list)

    def record(self, event: ExtractionCostEvent) -> None:
        self.total_calls += 1
        self.events.append(event)
