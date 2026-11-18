# build-hardening-kit

Make a green build mean something. One command adds format, lint, strict
types, secret scanning, a CI gate and (optionally) git hooks, governance and an
example architecture rule to a TypeScript, JavaScript, Python or Go repository.
The kit tests itself: every module is installed into sample repos and must pass
on a clean repo and fail on a planted problem, on Linux, macOS and Windows.

## Install

Needs [uv](https://docs.astral.sh/uv/) (for `uvx`) and git. Run from your repo root:

```bash
uvx copier copy --trust gh:yogi100x/build-hardening-kit .
```

You pick your stacks, a preset (`minimal` or `standard`) and, if you like,
single modules. `--trust` lets the kit's post-install task add npm scripts and
dev dependencies to `package.json` and Python dev tools with `uv add`
([`tasks/apply.py`](tasks/apply.py); read it first if you prefer).

| Module | What it adds | Preset |
|---|---|---|
| `format` | Prettier / ruff format / gofmt+gci check | minimal |
| `lint` | ESLint, ruff, golangci-lint; warnings are errors | minimal |
| `types` | strict `tsc`, `checkJs`, `mypy --strict`, `go vet` | minimal |
| `secrets` | gitleaks (CI scans the PR's own commits; the default branch scans all) | minimal |
| `ci` | one workflow, `.github/workflows/hardening.yml`, running the same entry points you run locally | minimal |
| `hooks` | pre-commit hooks (fast local feedback; CI is the gate) | standard |
| `governance` | CODEOWNERS, Dependabot, CodeQL | standard |
| `arch-rules` | example rule: no raw DB queries outside `dal/` ([DAL_POLICY.md](DAL_POLICY.md)) | off |

## Run the gate

| Stack | Locally (and in CI) |
|---|---|
| TypeScript / JavaScript | `npm run check && npm test` |
| Python | `uv run poe check && uv run poe test` |
| Go | `make check && make test` |

## Existing problems: debt only goes down

Turning strict checks on in an existing repo floods it with findings. Each tool
records today's findings once; new ones fail; fixed ones must be recorded:

- **ESLint:** `npx eslint --suppress-all .` writes `eslint-suppressions.json`.
  A new problem fails. Fixing a recorded one fails until
  `npx eslint --prune-suppressions .` lowers the count. The file is code:
  with `governance`, CODEOWNERS requires an owner to approve it growing.
- **ruff:** `uv run ruff check --add-noqa .` marks today's findings inline.
- **golangci-lint and semgrep:** pull requests fail only on issues new since the
  base branch; the default branch reports the rest without failing.

There is no switch in a PR's text that turns a gate off.

## Upgrade, change modules, remove

```bash
uvx copier update --trust                                  # newest kit release
uvx copier update --trust --data 'modules=["lint","types"]'  # change modules
```

Upgrades merge kit changes with your edits. Files you own (`eslint.config.mjs`,
`tsconfig.json`, `jsconfig.json`, `Makefile`, `ruff.toml`, `mypy.ini`,
`poe_tasks.toml`, `.prettierignore`, `.gitleaks.toml`) are created once and
never overwritten; each points at a kit-owned file (`*.hardening.*`) that
upgrades keep current. Removing a module deletes its files and the npm scripts
you did not change.

## The kit's own tests

`tests/` installs every module into sample repos (TypeScript, JavaScript,
Python, Go, and TypeScript + Python together) and proves each gate passes on a
clean repo and fails on a planted problem, with that rule's own message. It
also checks upgrades and the rendered workflows. See [tests/README.md](tests/README.md);
every bug found so far is in [tests/KNOWN_BUGS.md](tests/KNOWN_BUGS.md).

## More

- [GOOGLE_GRADE.md](GOOGLE_GRADE.md) — the review-process half of hardening.
- [docs/BRANCH_PROTECTION.md](docs/BRANCH_PROTECTION.md) — make the checks block merges.

Licence: MIT.
