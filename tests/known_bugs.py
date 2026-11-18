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
CASES: dict[tuple[str, str], tuple[str, str]] = {
    # Fixed in milestone 3, where the custom ratchet is replaced.
    ("ts", "ratchet-bypass"): ("missed", "B01"),
}

# Platform-specific overrides. B34: on Windows the ratchet's node reads Git
# Bash's /tmp as C:\tmp, so main's baseline is 0 and the clean repo is red.
CLEAN_RED_PLATFORM: dict[tuple[str, str], dict[str, str]] = {
    ("win", "ts"): {"lint": "B09", "ratchet": "B34"},
}
CASES_PLATFORM: dict[tuple[str, str, str], tuple[str, str]] = {
    ("win", "ts", "ratchet"): ("blocked", "B34"),
    ("win", "ts", "ratchet-shrink"): ("blocked", "B34"),
    ("win", "ts", "ratchet-bypass"): ("blocked", "B34"),
}


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
