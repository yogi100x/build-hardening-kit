"""Known kit bugs, as observed by the self-test.

Key: (stack, case). Value: the bug id and a one-line reason (see
tests/KNOWN_BUGS.md). Remove an entry in the same change that fixes the bug;
the self-test fails on XPASS so a fix cannot land without updating this list.
"""

from __future__ import annotations

import sys

KNOWN: dict[tuple[str, str], str] = {
    ("ts", "clean"): "B09 @repo/eslint-plugin not declared, lint cannot load",
    ("ts", "lint"): "B09 lint red on clean",
    ("ts", "dal"): "B09 lint red on clean",
    ("ts", "format"): "B31 no format check in the Node gate",
    ("ts", "secret"): "B32 ts variant has no secret scan",
    ("ts", "ratchet-bypass"): "B01 [skip-ratchet] in PR text switches the ratchet off",
    ("js", "clean"): "B09 plugin unresolvable; B17 checkJs type-checks the plugin",
    ("js", "lint"): "B09 lint red on clean",
    ("js", "dal"): "B09 lint red on clean",
    ("js", "types"): "B17 typecheck red on clean",
    ("js", "format"): "B31 no format check in the Node gate",
    ("python", "clean"): "B33 installed CI snippet fails the kit's own prettier hook",
    ("python", "dal"): "B33 pre-commit red on clean",
    ("python", "secret"): "B33 pre-commit red on clean",
    ("go", "clean"): "B04 golangci v1 config rejected by v2; v1.62.2 hook cannot read new Go; B33",
    ("go", "lint"): "B04 golangci-lint red on clean",
    ("go", "format"): "B04 golangci-lint red on clean; B26 no format check",
    ("go", "dal"): "B04 golangci-lint and pre-commit red on clean",
    ("go", "secret"): "B33 pre-commit red on clean",
    ("mono", "clean"): "B09 plugin unresolvable; B19 second variant's CI file silently skipped",
    ("mono", "ts-lint"): "B09 lint red on clean",
}

# Platform-specific entries: key (platform prefix, stack, case).
KNOWN_PLATFORM: dict[tuple[str, str, str], str] = {}


def expected_failure(stack: str, case: str) -> str | None:
    for (plat, s, c), reason in KNOWN_PLATFORM.items():
        if sys.platform.startswith(plat) and (s, c) == (stack, case):
            return reason
    return KNOWN.get((stack, case))
