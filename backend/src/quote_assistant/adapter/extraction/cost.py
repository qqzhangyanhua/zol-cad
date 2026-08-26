from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Protocol

DEFAULT_MAX_COST_EVENTS = 1000


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
    """Process-local counter. events is bounded so a long-running process cannot leak."""

    total_calls: int = 0
    max_events: int = DEFAULT_MAX_COST_EVENTS
    events: deque[ExtractionCostEvent] = field(default_factory=deque)

    def __post_init__(self) -> None:
        self.events = deque(self.events, maxlen=self.max_events)

    def record(self, event: ExtractionCostEvent) -> None:
        self.total_calls += 1
        if self.events.maxlen != self.max_events:
            self.events = deque(self.events, maxlen=self.max_events)
        self.events.append(event)
