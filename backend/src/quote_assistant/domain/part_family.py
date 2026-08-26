from __future__ import annotations

from collections.abc import Sequence

from quote_assistant.domain.extraction import ExtractedField

# PROVISIONAL — ticket 01 is not closed. No factory samples, no researched family.
# This single named constant exists so the mechanism can distinguish 目标零件族
# vs 非目标 / 未知. It is NOT a research conclusion and does not close ADR-0008.
TARGET_PART_FAMILY_ID = "provisional-target-family"
PROVISIONAL_OTHER_PART_FAMILY_ID = "provisional-other-family"
UNKNOWN_PART_FAMILY_ID = "unknown"

EXPERIMENTAL_MARK_TEXT = "实验性、不保证"

# Fixture-atlas slot prefixes from ticket 01's research framework
# (`.scratch/.../05-fixture-atlas.md`). FX-T = 目标族槽, FX-N = 非目标族槽.
# Filename path is for seam-1 / local fixture only. Real factory names never
# contain these substrings.
_TARGET_FIXTURE_SLOT = "FX-T"
_NON_TARGET_FIXTURE_SLOT = "FX-N"


def classify_part_family_from_content(
    *,
    extracted_fields: Sequence[ExtractedField] | None = None,
    engine_family_signal: str | None = None,
) -> str:
    """Content-based 零件族判定.

    Ticket 01 has not supplied criteria (no factory samples, no selected family).
    Always returns unknown. Do not invent heuristics such as "looks like a shaft".
    """
    del extracted_fields, engine_family_signal
    return UNKNOWN_PART_FAMILY_ID


def classify_part_family_from_fixture_filename(input_drawing_id: str) -> str:
    """Filename / fixture-atlas slot stub. Seam-1 and local fixture only."""
    haystack = input_drawing_id.upper()
    if _TARGET_FIXTURE_SLOT in haystack:
        return TARGET_PART_FAMILY_ID
    if _NON_TARGET_FIXTURE_SLOT in haystack:
        return PROVISIONAL_OTHER_PART_FAMILY_ID
    return UNKNOWN_PART_FAMILY_ID


def classify_part_family(
    input_drawing_id: str,
    *,
    allow_fixture_filename: bool = False,
    extracted_fields: Sequence[ExtractedField] | None = None,
    engine_family_signal: str | None = None,
) -> str:
    """Prefer content when ticket 01 supplies criteria; else fixture filename if allowed."""
    content = classify_part_family_from_content(
        extracted_fields=extracted_fields,
        engine_family_signal=engine_family_signal,
    )
    if content != UNKNOWN_PART_FAMILY_ID:
        return content
    if allow_fixture_filename:
        return classify_part_family_from_fixture_filename(input_drawing_id)
    return UNKNOWN_PART_FAMILY_ID


def adopt_content_classified_family(
    current_family_id: str,
    *,
    extracted_fields: Sequence[ExtractedField] | None = None,
    engine_family_signal: str | None = None,
) -> str:
    """Keep the persisted 零件族 until the content hook returns a real class."""
    classified = classify_part_family_from_content(
        extracted_fields=extracted_fields,
        engine_family_signal=engine_family_signal,
    )
    if classified == UNKNOWN_PART_FAMILY_ID:
        return current_family_id
    return classified


def is_target_part_family(family_id: str) -> bool:
    return family_id == TARGET_PART_FAMILY_ID


def experimental_mark_for(family_id: str) -> str | None:
    """Non-target and unknown results carry 实验性、不保证. Target family does not."""
    if is_target_part_family(family_id):
        return None
    return EXPERIMENTAL_MARK_TEXT
