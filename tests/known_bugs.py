"""Known kit bugs, as observed by the self-test. Ids are in KNOWN_BUGS.md.

The self-test asserts these exact outcomes, so the list cannot go stale: a fix
changes the outcome and the run fails until the entry here is updated in the
same change, and a new break that is not listed fails straight away.
"""

from __future__ import annotations

import sys

# Gate steps expected to be red on the freshly installed, untouched repo.
CLEAN_RED: dict[str, dict[str, str]] = {}

# Outcome of a planted case when it is not the healthy one. Outcomes:
#   blocked     - no expected step is usable (absent from the gate, or red on clean)
#   missed      - the change is planted and no expected step catches it
#   false-alarm - a legitimate change (must_pass) is refused
CASES: dict[tuple[str, str], tuple[str, str]] = {}

# Platform-specific overrides: (sys.platform prefix, stack[, case]).
CLEAN_RED_PLATFORM: dict[tuple[str, str], dict[str, str]] = {}
CASES_PLATFORM: dict[tuple[str, str, str], tuple[str, str]] = {}


def expected_clean(stack: str) -> dict[str, str]:
    for (plat, s), red in CLEAN_RED_PLATFORM.items():
        if sys.platform.startswith(plat) and s == stack:
            return red
    return CLEAN_RED.get(stack, {})


def expected_case(stack: str, case: str, healthy: str) -> tuple[str, str]:
    for (plat, s, c), outcome in CASES_PLATFORM.items():
        if sys.platform.startswith(plat) and (s, c) == (stack, case):
            return outcome
    return CASES.get((stack, case), (healthy, ""))
