from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HardGateStatus:
    """One ADR-0005 hard gate as currently written in ADR-0009. No invented verdict."""

    key: str
    name: str
    verdict: str
    evidence: str


@dataclass(frozen=True)
class DrawingStorageNotice:
    """Where 零件图 bytes live in *this* deployment. Runtime config, not a vendor promise."""

    backend: str
    location_summary: str
    notes: str


@dataclass(frozen=True)
class ConfidentialityNotice:
    """Admin-facing facts for customer security questionnaires.

    Values come from ADR-0009 + current runtime config. Empty / 待填 cells stay empty.
    """

    ticket_02_closed: bool
    ticket_02_status: str
    adr_status: str
    adr_path: str
    research_notes_path: str
    vendor_selected: bool
    selected_vendor: str | None
    vendor_decision_line: str
    hard_gates: tuple[HardGateStatus, ...]
    implementation_constraints: tuple[str, ...]
    drawing_storage: DrawingStorageNotice
    processor_summary: str
    current_extraction_engine: str
    used_for_training_statement: str
    dpa_statement: str
    caveats: tuple[str, ...]
