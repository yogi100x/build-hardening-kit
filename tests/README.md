# Self-test

Proves the kit does what it says. For each stack (`ts`, `js`, `python`, `go`,
and a `mono` repo with TypeScript and Python together) the self-test:

1. copies a small fixture repo from `tests/fixtures/<stack>/` into a temp dir
   and makes it a git repo with an `origin/main`;
2. installs the kit the way the README tells a user to;
3. runs the stack's gate (the commands the kit documents) and expects it to
   **pass** on the clean repo;
4. plants one violation at a time on a `pr` branch (lint, types, format,
   tests, raw DB query, secret, ratchet growth) and expects the step that
   should catch it to **fail**. A step that is already red on the clean repo
   cannot prove anything, so the case fails rather than passing by accident.

## Run it

```bash
uv run --python 3.12 pytest              # everything
uv run --python 3.12 pytest -k python    # one stack
```

Needs `node`/`npm`, `uv`, `go`, `golangci-lint` (v2) and `bash` on `PATH`.
`pre-commit` and `semgrep` are fetched with `uvx` when not installed.
A missing tool skips locally and fails in CI (`BHK_REQUIRE_TOOLS=1`).

CI runs it on Ubuntu, macOS and Windows on every pull request, on `main`,
and nightly, so a new upstream tool release that breaks the kit shows up
within a day (`.github/workflows/self-test.yml`).

## Known bugs

`KNOWN_BUGS.md` lists every bug with an id; `known_bugs.py` marks the cases
that fail because of one. Those cases are expected failures. When a fix makes
one pass, the run fails (strict xfail) until the marker is removed in the
same change, so the list always matches reality.

## Adding a stack or a check

Add a fixture under `tests/fixtures/<stack>/`, then a `Stack` entry in
`stacks.py`: setup steps, gate steps (label, command, directory), and the
violations with the gate label expected to catch each.
