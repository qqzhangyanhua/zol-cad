from __future__ import annotations

# PROVISIONAL — ticket 01 is not closed. No factory samples, no researched family.
# This single named constant exists so the mechanism can distinguish 目标零件族
# vs 非目标 / 未知. It is NOT a research conclusion and does not close ADR-0008.
TARGET_PART_FAMILY_ID = "provisional-target-family"
PROVISIONAL_OTHER_PART_FAMILY_ID = "provisional-other-family"
UNKNOWN_PART_FAMILY_ID = "unknown"

EXPERIMENTAL_MARK_TEXT = "实验性、不保证"

# Fixture-atlas slot prefixes from ticket 01's research framework
# (`.scratch/.../05-fixture-atlas.md`). FX-T = 目标族槽, FX-N = 非目标族槽.
# This is a filename/id stub, not a visual classifier and not a chosen machining family.
_TARGET_FIXTURE_SLOT = "FX-T"
_NON_TARGET_FIXTURE_SLOT = "FX-N"


def classify_part_family(input_drawing_id: str) -> str:
    """Persist a 零件族 from the fixture id / filename. Honest stub, not researched."""
    haystack = input_drawing_id.upper()
    if _TARGET_FIXTURE_SLOT in haystack:
        return TARGET_PART_FAMILY_ID
    if _NON_TARGET_FIXTURE_SLOT in haystack:
        return PROVISIONAL_OTHER_PART_FAMILY_ID
    return UNKNOWN_PART_FAMILY_ID


def is_target_part_family(family_id: str) -> bool:
    return family_id == TARGET_PART_FAMILY_ID


def experimental_mark_for(family_id: str) -> str | None:
    """Non-target and unknown results carry 实验性、不保证. Target family does not."""
    if is_target_part_family(family_id):
        return None
    return EXPERIMENTAL_MARK_TEXT
