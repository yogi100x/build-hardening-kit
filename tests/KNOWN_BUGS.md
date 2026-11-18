# Known bugs

Every bug found in the kit, with an id. `tests/known_bugs.py` records the exact
outcome each bug causes in the self-test (which step is red on a clean install,
which planted case is blocked or missed). The self-test asserts those outcomes,
so a fix must update the entry in the same change, and anything new fails.

"Observed" = the self-test reproduces it today. "Review" = found by reading the
code; it gets a self-test case when it is fixed.

| Id | Bug | Where | Source |
|---|---|---|---|
| B01 | `[skip-ratchet]` anywhere in a PR title or body switches the ratchet off; any author, or injected text, can do it | `shared/.github/scripts/check-baseline-shrinkage.sh` | Observed |
| B02 | Actions pinned by tag, not commit SHA; Node `ci.yml` has no `permissions:` block | `shared/.github/workflows/ci.yml`, `polyglot/ci.yml`, `go/ci.snippet.yml`, `python/ci.snippet.yml`, `.github/workflows/codeql.yml` | Review |
| B03 | semgrep unpinned (`pip install semgrep`, local pre-commit hook) | `polyglot/ci.yml`, `polyglot/.pre-commit-config.yaml` | Review |
| B04 | golangci config uses the v1 schema (v2 refuses it); pre-commit pins v1.62.2, which cannot read current Go export data | `go/.golangci.yml`, `polyglot/.pre-commit-config.yaml` | Observed |
| B05 | Baseline generator counts with a regex, the rule with the AST; first run disagrees | `shared/eslint-plugin-template/scripts/generate-baseline.mjs` | Review |
| B06 | CI repeats commands instead of calling one local entry point; only Go has a Makefile | all CI files | Review |
| B07 | Python CI installs no project dependencies or lockfile; Node CI makes tests optional (`--if-present`) | `python/ci.snippet.yml`, `shared/.github/workflows/ci.yml` | Review |
| B08 | Env check reads only `process.env.X` (misses `process.env["X"]`, destructuring, `import.meta.env`, `export X=` lines, other languages) | `shared/.github/scripts/check-env-schema.sh` | Review |
| B09 | `@repo/eslint-plugin` is copied but never declared as a dependency, so ESLint cannot load it | `install.sh`, `ts/package.snippet.json`, `js/package.snippet.json` | Observed |
| B10 | `FORCE=1` reinstall nests copied directories inside the old ones; `chmod` runs even when copies were skipped | `install.sh` | Review |
| B11 | Ratchet fails open: unreadable JSON counts as 0, missing main baseline counts as equal, needs `node`; semgrep on push to main compares main with itself | `check-baseline-shrinkage.sh`, `polyglot/ci.yml` | Review |
| B12 | CodeQL passes `language:` where the action expects `languages:` | `.github/workflows/codeql.yml` | Review |
| B13 | DAL policy and rule disagree: `data_access/` vs `data-access/`; Prisma `findMany` promised but not caught | `DAL_POLICY.md`, `no-raw-db-client.js` | Review |
| B14 | Go/Python CI snippets are installed outside `.github/workflows/`, so they never run; snippet files are left in the repo root | `install.sh` | Review |
| B15 | `gitleaks-action` needs a licence key for organisation-owned repos | `polyglot/ci.yml` | Review |
| B16 | Type-checked ESLint rules applied to the plugin's own `.js` files, which `tsconfig` does not include | `ts/eslint.config.mjs` | Review |
| B17 | `jsconfig.json` includes `packages/`, so `checkJs` type-checks the kit's plugin and fails | `js/jsconfig.json` | Observed |
| B18 | `go` install skips `Makefile.snippet`; its next-steps text says `pre-commit install` though nothing installs pre-commit; usage omits `google` | `install.sh` | Review |
| B19 | Installing a second variant silently skips its `ci.yml`; a TS+Python repo gets only one stack in CI | `install.sh` | Observed |
| B20 | `GOOGLE_GRADE.md` cites rules and a coverage gate the kit does not have | `GOOGLE_GRADE.md` | Review |
| B21 | CODEOWNERS placeholder owner makes GitHub skip the code-owner requirement silently | `.github/CODEOWNERS` | Review |
| B22 | Rule's baseline key is relative to `process.cwd()` (differs between lint-staged, monorepo packages and CI); `context.getFilename()` is deprecated | `no-raw-db-client.js` | Review |
| B23 | Ratchet counts by position: a new call above old ones flags an old line | `no-raw-db-client.js` | Review |
| B24 | `/* eslint @repo/no-raw-db-client: off */` bypasses `no-dal-disable` | `no-dal-disable.js` | Review |
| B25 | `rules.go` is dropped by `go mod tidy` without a `tools.go` import, so ruleguard cannot load | `go/rules.go` | Review |
| B26 | `make check` runs `gofmt -w` (writes); no format check in CI; `new-from-rev` set twice | `go/Makefile.snippet`, `go/.golangci.yml` | Observed |
| B27 | `mirrors-prettier` is archived and pinned to an alpha | `polyglot/.pre-commit-config.yaml` | Review |
| B28 | semgrep secret rule fires on tests and examples (no test-path exclude) | `polyglot/semgrep/rules.yml` | Review |
| B29 | `pip install` without `setup-python` | `polyglot/ci.yml` | Review |
| B30 | `cancel-in-progress` also cancels runs on `main` | `shared/.github/workflows/ci.yml` | Review |
| B31 | Node variants never check formatting in CI (Prettier only runs on staged files) | `shared/.github/workflows/ci.yml`, `*/package.snippet.json` | Observed |
| B32 | TS/JS variants install no secret scanning | `install.sh` | Observed |
| B33 | The CI snippet the kit installs fails the kit's own Prettier hook, so `pre-commit run --all-files` is red right after install | `install.sh`, `polyglot/.pre-commit-config.yaml` | Observed |
| B34 | On Windows the ratchet reads main's baseline from `/tmp` through `node`, which resolves it to `C:\tmp`; main reads as 0, so lowering debt is refused | `check-baseline-shrinkage.sh` | Observed (Windows) |
