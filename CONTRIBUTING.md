# Contributing

## The one rule

Every change is proved by the self-test. A new module or check needs a fixture
case that **passes on a clean repo and fails on a planted problem**, with the
rule's own message in the output. A fix needs a case that failed before it.

## Run the self-test

```bash
uv run --python 3.12 pytest              # everything (a few minutes)
uv run --python 3.12 pytest -k python    # one stack
uv run --python 3.12 pytest tests/test_static.py   # rendered template only (seconds)
```

Tools needed are listed in [tests/README.md](tests/README.md). CI runs the same
on Linux, macOS and Windows, and nightly (Node LTS, Go stable and npm ranges
move between runs; other tools are pinned and bumped deliberately).

## Layout

| Path | What |
|---|---|
| `copier.yml` | questions, presets, computed flags (template delimiters are `[[ ]]` and `[% %]`, because GitHub Actions uses `${{ }}`) |
| `template/` | rendered into users' repos; file names starting with `[% if ... %]` exist only when that module is on |
| `tasks/apply.py` | post-install task (standard library only) |
| `tests/` | the self-test, fixtures, known bugs |
| `docs/modules/` | one page per module |
| `docs/decisions/` | why the kit is built this way |

## Adding a module

1. Add it to `modules` in `copier.yml` and a computed flag if templates need one.
2. Add its files under `template/`, kit-owned or user-owned (`_skip_if_exists`).
3. Add fixture cases in `tests/stacks.py` and, for rendered-only checks,
   `tests/test_static.py`.
4. Add `docs/modules/<name>.md` and a row in the README.
5. Record any bug you find in `tests/KNOWN_BUGS.md`.

## Pull requests

Say what changed, which tests ran and their results. Pin every new action to a
commit SHA and every new tool to an exact version.
