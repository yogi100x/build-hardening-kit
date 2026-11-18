# build-hardening-kit

Make a green build mean something. One command adds format, lint, strict
types, secret scanning, a CI gate and (optionally) git hooks, governance and an
example architecture rule to a TypeScript, JavaScript, Python or Go repository.
The kit tests itself: every module is installed into sample repos and must pass
on a clean repo and fail on a planted problem, on Linux, macOS and Windows.

## Quickstart

Needs [uv](https://docs.astral.sh/uv/) (for `uvx`) and git. In a clean working
tree at your repo root:

```bash
uvx copier copy --trust gh:yogi100x/build-hardening-kit .
```

Answer the questions (stacks, preset, modules). Without a terminal (scripts,
CI, agents), pass the answers instead:

```bash
uvx copier copy --trust --defaults \
  --data 'stacks=["ts"]' --data preset=standard \
  gh:yogi100x/build-hardening-kit .
```

| Answer | Values |
|---|---|
| `stacks` | list of `ts`, `js`, `python`, `go` (not `ts` and `js` together) |
| `preset` | `minimal`, `standard` (default) |
| `modules` | list; overrides the preset: `format`, `lint`, `types`, `secrets`, `ci`, `hooks`, `governance`, `agents`, `arch-rules` |
| `node_package_manager` | `npm` (default), `pnpm`, `yarn` |
| `default_branch` | default `main` |
| `go_module` | your module path from `go.mod` |
| `code_owners`, `required_reviews`, `require_codeql` | see [governance](docs/modules/governance.md) |

A red `conflict … skip` line during install means the kit kept a file you
already had; see NOT WIRED below. Then:

| Stack | First run | Then commit |
|---|---|---|
| TypeScript / JavaScript | `npm run format` once (existing files get reformatted), existing lint problems: `npx eslint --suppress-all .` once, then `npm run check && npm test` | everything, incl. your lockfile (`package-lock.json`, `pnpm-lock.yaml` or `yarn.lock`) and `eslint-suppressions.json` |
| Python (uv) | `uv run ruff format .` once; existing type errors: annotate them, or fence old code (see [types](docs/modules/types.md)); then `uv run poe check && uv run poe test` | everything, incl. `uv.lock` |
| Go | needs [golangci-lint v2](https://golangci-lint.run/docs/welcome/install/) and make; `make fmt` once, then `make check && make test` | everything |

With `hooks`: `uvx pre-commit install`. With `governance`:
`.github/hardening/protect-branch.sh --dry-run`, then without `--dry-run`, to
make the checks block merges.

If the install ends with **NOT WIRED**, your repo already had that config file;
add the one line it shows.

`--trust` lets the kit's post-install task add npm scripts and dev dependencies
to `package.json` and Python dev tools with `uv add`
([`tasks/apply.py`](tasks/apply.py); read it first if you prefer).

## Modules

| Module | What it adds | Preset |
|---|---|---|
| [`format`](docs/modules/format.md) | Prettier / ruff format / gofmt+gci check | minimal |
| [`lint`](docs/modules/lint.md) | ESLint, ruff, golangci-lint; warnings are errors | minimal |
| [`types`](docs/modules/types.md) | strict `tsc`, `checkJs`, `mypy --strict`, `go vet` | minimal |
| [`secrets`](docs/modules/secrets.md) | gitleaks (CI scans the PR's own commits; the default branch scans all) | minimal |
| [`ci`](docs/modules/ci.md) | one workflow, `.github/workflows/hardening.yml`, running the same entry points you run locally | minimal |
| [`hooks`](docs/modules/hooks.md) | pre-commit hooks (fast local feedback; CI is the gate) | standard |
| [`governance`](docs/modules/governance.md) | CODEOWNERS, Dependabot, CodeQL, a PR template, and a script that makes exactly these checks block merges | standard |
| [`agents`](docs/modules/agents.md) | `AGENTS.md` (read by most coding agents; `CLAUDE.md` points to it) with the gate commands and rules | standard |
| [`arch-rules`](docs/modules/arch-rules.md) | example rule: no raw DB queries outside `dal/` | off |

## Tested with

| | |
|---|---|
| OS | Linux, macOS, Windows (GitHub-hosted runners; Windows uses Git Bash) |
| Node | current LTS; ESLint 9.39+, TypeScript 5.9, Prettier 3.10 |
| Python | 3.12 with uv; ruff, mypy, pytest, poethepoet |
| Go | stable; golangci-lint v2.15 |
| Tools | copier 9.19, gitleaks 8.30, semgrep 1.186, pre-commit 4.7 |
| CI | GitHub Actions. Other CI: each job is one or two commands to copy |

The self-test also runs nightly. Node LTS, Go stable and the npm version
ranges move between runs, so breaking releases there show up within a day;
the pinned tools above change only when the kit bumps them.

## Run the gate

| Stack | Locally (CI's per-stack job runs the same) |
|---|---|
| TypeScript / JavaScript | `npm run check && npm test` |
| Python | `uv run poe check && uv run poe test` |
| Go | `make check && make test` |

The secret scan and the semgrep rules run in CI and in the git hooks, not in
these commands.

## Existing problems: debt only goes down

Turning strict checks on in an existing repo floods it with findings. Each tool
records today's findings once; new ones fail; fixed ones must be recorded:

- **ESLint:** `npx eslint --suppress-all .` writes `eslint-suppressions.json`.
  A new problem fails. Fixing a recorded one fails until
  `npx eslint --prune-suppressions .` lowers the count. The file is code:
  with `governance`, CODEOWNERS requires an owner to approve it growing.
- **ruff:** `uv run ruff check --add-noqa .` marks today's findings inline.
- **golangci-lint and semgrep:** pull requests fail only on issues new since the
  base branch; the default branch reports the rest without failing. Locally,
  `make lint` compares with `origin/<default branch>`; in a repo with no remote
  yet, every issue counts as new.
- **mypy:** annotate, or fence old modules with `ignore_errors` sections
  ([types](docs/modules/types.md)).

There is no switch in a PR's text that turns a gate off.

## Upgrade, change modules, remove

```bash
uvx copier update --trust                                  # newest kit release
uvx copier update --trust --data 'modules=["lint","types"]'  # change modules
```

Upgrades merge kit changes with your edits. Files you own are never
overwritten: `eslint.config.mjs`, `tsconfig.json`, `jsconfig.json`, `Makefile`,
`ruff.toml`, `mypy.ini`, `poe_tasks.toml`, `.prettierignore`, `.gitleaks.toml`,
`.gitattributes`, `AGENTS.md`, `CLAUDE.md`, `.github/pull_request_template.md`.
When the kit creates one of the first five, it points at a kit-owned file
(`*.hardening.*`, `hardening.mk`) that upgrades keep current; the others are
plain starting points. When your repo already has one, the kit keeps yours and
lists it under **NOT WIRED** at the end of the install, with the one line to add
— until you add it, that check runs without the kit's rules. Removing a module
deletes its files and the npm scripts you did not change.

If your repo already has a file the kit manages itself (`.pre-commit-config.yaml`,
`.golangci.yml`, `.prettierrc.json`, `.github/dependabot.yml`,
`.github/CODEOWNERS`), copier asks before replacing it, so run the first install
interactively (or move yours aside and merge it back afterwards).

Node: npm, pnpm and yarn are supported (`node_package_manager`); CI installs
from that lockfile.

## The kit's own tests

`tests/` installs every module into sample repos (TypeScript, JavaScript,
Python, Go, and TypeScript + Python together) and proves each gate passes on a
clean repo and fails on a planted problem, with that rule's own message. It
also checks upgrades and the rendered workflows. See [tests/README.md](tests/README.md);
every bug found so far is in [tests/KNOWN_BUGS.md](tests/KNOWN_BUGS.md).

## More

- [GOOGLE_GRADE.md](GOOGLE_GRADE.md) — the review-process half of hardening.
- [docs/BRANCH_PROTECTION.md](docs/BRANCH_PROTECTION.md) — make the checks block merges.
- [docs/decisions/](docs/decisions/README.md) — why the kit is built this way.
- [CHANGELOG.md](CHANGELOG.md), [CONTRIBUTING.md](CONTRIBUTING.md),
  [SECURITY.md](SECURITY.md) (report vulnerabilities privately).

Licence: MIT.
