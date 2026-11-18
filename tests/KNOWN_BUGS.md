# Known bugs

Every bug found in the kit, with an id. `tests/known_bugs.py` records the exact
outcome each open bug causes in the self-test (which step is red on a clean
install, which planted case is blocked or missed). The self-test asserts those
outcomes, so a fix must update the entry in the same change, and anything new
fails.

Status: **Fixed (M2)** with the check that proves it; **M3** = fixed when the
custom ratchet and installer are replaced (milestone 3), so not patched here.

| Id | Bug | Status |
|---|---|---|
| B01 | `[skip-ratchet]` anywhere in a PR title or body switches the ratchet off; any author, or injected text, can do it | M3 — self-test `ts-ratchet-bypass` records it as `missed` |
| B02 | Actions pinned by tag, not commit SHA; Node workflow had no `permissions:` | Fixed (M2) — `test_static`: SHA pins, permissions |
| B03 | semgrep unpinned (`pip install semgrep`, local pre-commit hook) | Fixed (M2) — `test_static::test_no_unpinned_installs` |
| B04 | golangci config used the v1 schema (v2 refuses it); pre-commit pinned v1.62.2 | Fixed (M2) — `go-clean`, `go-lint`, `test_golangci_config_is_v2` |
| B05 | Baseline generator counts with a regex, the rule with the AST | M3 (custom ratchet replaced by native suppressions) |
| B06 | No single local entry point | Partly: `npm run check`, `make check`. Rest in M3 |
| B07 | Python CI installed no project deps or lockfile; Node CI made tests optional | Fixed (M2) — `uv sync --locked`, required `npm test`; `ts-test` |
| B08 | Env check read only `process.env.X` | Partly (M2): also `process.env["X"]`, `import.meta.env.X`, `export X=` (`ts-env`). Destructuring and non-JS languages: M3 |
| B09 | `@repo/eslint-plugin` never declared as a dependency | Fixed (M2) — `ts-clean`, `js-clean`, `mono-clean` |
| B10 | `FORCE=1` reinstall nested directories; `chmod` ran on skipped copies | Fixed (M2) in `install.sh`; installer replaced in M3 |
| B11 | Ratchet fails open (unreadable JSON = 0, missing main baseline = equal, needs `node`); semgrep on main compared main with itself | Semgrep part fixed (M2: report-only full scan on main, see B37). Ratchet part: M3 |
| B12 | CodeQL passed `language:` instead of `languages:` | Fixed (M2) — `test_codeql_input_name` |
| B13 | DAL policy and rule disagreed on directories and Prisma | Fixed (M2) — `ts-dal-prisma`, `ts-dal-dir-exempt`, `test_dal_directories_agree` |
| B14 | Go/Python CI snippets installed outside `.github/workflows/` | Fixed (M2) — full workflows installed as `hardening-<stack>.yml` |
| B15 | `gitleaks-action` needs a licence key for organisation repos | Fixed (M2) — gitleaks CLI image pinned by digest |
| B16 | Type-checked ESLint rules applied to plain `.js` files | Fixed (M2) — typed rules scoped to `*.ts`; `ts-clean` |
| B17 | `jsconfig.json` type-checked the kit's own plugin | Fixed (M2) — `js-clean`, `js-types` |
| B18 | `go` install skipped the Makefile; wrong next-steps text; usage omitted `google` | Fixed (M2) |
| B19 | A second variant's CI file was silently skipped | Fixed (M2) — `mono-clean` |
| B20 | `GOOGLE_GRADE.md` cited rules and a coverage gate the kit does not have | Fixed (M2) — `test_docs_cite_only_real_rules` |
| B21 | CODEOWNERS placeholder owner silently disabled the code-owner requirement | Fixed (M2) — ships commented out; `test_codeowners_has_no_live_placeholder` |
| B22 | Rule's baseline key depends on `process.cwd()`; `context.getFilename()` deprecated | M3 |
| B23 | Ratchet counts by position: a new call above old ones flags an old line | M3 |
| B24 | `/* eslint @repo/no-raw-db-client: off */` bypasses `no-dal-disable` | M3 (with the DAL rule's move to an optional module) |
| B25 | Claimed: `go mod tidy` drops the ruleguard DSL | Not reproduced: `go-dal` runs `go mod tidy` and ruleguard still fires. The DSL must be added once (`go get .../dsl`); install now says so |
| B26 | `make check` rewrote files (`gofmt -w`); no format check; `new-from-rev` set twice | Fixed (M2) — `go-format`, `test_golangci_config_is_v2` |
| B27 | `mirrors-prettier` archived, pinned to an alpha | Fixed (M2) — maintained mirror; `test_no_archived_hook_repos` |
| B28 | semgrep secret rule fired on tests and fixtures | Fixed (M2) — test paths excluded |
| B29 | `pip install` without `setup-python` | Fixed (M2) — `uvx semgrep@<version>` |
| B30 | `cancel-in-progress` cancelled runs on `main` | Fixed (M2) — `test_main_runs_never_cancelled` |
| B31 | Node variants never checked formatting in CI | Fixed (M2) — `format:check`; `ts-format`, `js-format` |
| B32 | TS/JS variants had no secret scanning | Fixed (M2) — gitleaks job; `ts-secret` |
| B33 | Installed files failed the kit's own Prettier hook | Fixed (M2) — `python-clean`, `test_installable_files_pass_prettier` |
| B34 | On Windows the ratchet reads main's baseline from `/tmp` via `node` (`C:\tmp`), so lowering debt is refused | M3 — self-test `ts-ratchet-shrink` records it on Windows |
| B35 | `FORCE=1` reinstall deleted whole directories (user hooks, custom rules, the recorded debt baseline) | Fixed (M2) — directories merged, baseline kept |
| B36 | Gitleaks scanned all history on every PR: one old, rotated secret failed every PR forever | Fixed (M2) — PRs scan their own commits; `test_gitleaks_prs_scan_only_their_commits` |
| B37 | On main, "only new issues" compared main with itself (golangci) or full scans failed main on existing debt (semgrep) | Fixed (M2) — main reports debt without failing; `test_main_reports_debt_without_failing` |
| B38 | The pre-commit ruff (pinned v0.8.4) and CI's locked ruff could disagree on formatting | Fixed (M2) — hook runs `uv run ruff`; `test_python_hooks_use_project_ruff` |
| B39 | `jsconfig.json` includes only `src`, `apps`, `packages`; code elsewhere is not type-checked (or TS18003) | M3 |
