# Self-test

Proves the kit does what it says. For each stack (`ts`, `js`, `python`, `go`,
and a `mono` repo with TypeScript and Python together) the self-test:

1. copies a small fixture repo from `tests/fixtures/<stack>/` into a temp dir
   and makes it a git repo with an `origin/main`;
2. installs the kit the way the README tells a user to (`copier copy --trust`,
   all modules, plus recorded lint debt for the TypeScript repo);
3. runs the stack's gate (the commands the kit documents) and expects it to
   **pass** on the clean repo;
4. plants one change at a time on a `pr` branch and checks the outcome:
   - a violation (lint, types, format, tests, raw DB query, secret, debt
     growth or an unrecorded fix, a `[skip-ratchet]` text in the PR) must make the step meant to
     catch it **fail**, with that rule's own id or message in the output, so a
     crash or an unrelated rule never counts as caught;
   - a legitimate change (debt going down) must **pass**.

   A step already red on the clean repo cannot prove anything, so such a case
   is reported as `blocked`, never as caught.

Two more files cover what a fixture run cannot see: `test_upgrade.py` (a kit
release merged over the user's edits; removing a module) and `test_static.py`
(the rendered template for every stack and preset: pinned actions, least
privilege, valid YAML/JSON, no live placeholder owners).

## Run it

```bash
uv run --python 3.12 pytest              # everything
uv run --python 3.12 pytest -k python    # one stack
```

Needs `node`/`npm`, `uv`, `go`, `golangci-lint` (v2), `gitleaks`, `make` (not on
Windows) and git on `PATH`. `copier`, `pre-commit` and `semgrep` are fetched
with `uvx`, at pinned versions, when not installed.
A missing tool skips locally and fails in CI (`BHK_REQUIRE_TOOLS=1`).

CI runs it on Ubuntu, macOS and Windows on every pull request, on `main`,
and nightly, so a new upstream tool release that breaks the kit shows up
within a day (`.github/workflows/self-test.yml`).

## Known bugs

`KNOWN_BUGS.md` lists every bug with an id; `known_bugs.py` records the exact
outcome each one causes today (steps red on a clean install; cases `blocked`,
`missed` or `false-alarm`). The self-test asserts those outcomes. When a fix
changes one, the run fails until the entry is updated in the same change, and
an outcome nobody recorded fails at once, so the list always matches reality.

## Adding a stack or a check

Add a fixture under `tests/fixtures/<stack>/`, then a `Stack` entry in
`stacks.py`: setup steps, gate steps (label, command, directory), and the
cases with the gate labels expected to react and the message that proves the
right rule fired.
