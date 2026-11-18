# Known bugs

Every bug found in the kit, with an id. `tests/known_bugs.py` records the exact
outcome each open bug causes in the self-test (which step is red on a clean
install, which planted case is blocked or missed). The self-test asserts those
outcomes, so a fix must update the entry in the same change, and anything new
fails.

Status: **Fixed (M2/M3)** with the check that proves it. No bug is open.

| Id | Bug | Status |
|---|---|---|
| B01 | `[skip-ratchet]` anywhere in a PR title or body switches the ratchet off; any author, or injected text, can do it | Fixed (M3) — custom ratchet replaced by ESLint suppressions; no text bypass exists (`ts-debt-bypass`, `test_no_custom_ratchet_left`) |
| B02 | Actions pinned by tag, not commit SHA; Node workflow had no `permissions:` | Fixed (M2) — `test_static`: SHA pins, permissions |
| B03 | semgrep unpinned (`pip install semgrep`, local pre-commit hook) | Fixed (M2) — `test_static::test_no_unpinned_installs` |
| B04 | golangci config used the v1 schema (v2 refuses it); pre-commit pinned v1.62.2 | Fixed (M2) — `go-clean`, `go-lint`, `test_golangci_config_is_v2` |
| B05 | Baseline generator counts with a regex, the rule with the AST | Fixed (M3) — generator deleted; ESLint records its own findings (`npx eslint --suppress-all`) |
| B06 | No single local entry point | Fixed (M3) — `npm run check`, `uv run poe check`, `make check`; CI runs the same (`*-clean` entry steps) |
| B07 | Python CI installed no project deps or lockfile; Node CI made tests optional | Fixed (M2) — `uv sync --locked`, required `npm test`; `ts-test` |
| B08 | Env check read only `process.env.X` | Partly fixed in M2. The bash, JS-only check is not carried into the copier kit (M3); a cross-platform, all-language version is a later module |
| B09 | `@repo/eslint-plugin` never declared as a dependency | Fixed (M2) — `ts-clean`, `js-clean`, `mono-clean` |
| B10 | `FORCE=1` reinstall nested directories; `chmod` ran on skipped copies | Fixed (M2); `install.sh` replaced by copier in M3 (`test_upgrade`) |
| B11 | Ratchet fails open (unreadable JSON = 0, missing main baseline = equal, needs `node`); semgrep on main compared main with itself | Fixed — semgrep in M2 (B37); ratchet script deleted in M3. ESLint fails on growth and on unrecorded shrinkage (`ts-debt-grow`, `ts-debt-shrink-unrecorded`, `ts-debt-shrink`) |
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
| B22 | Rule's baseline key depends on `process.cwd()`; `context.getFilename()` deprecated | Fixed (M3) — no baseline in the rule; uses `context.filename` |
| B23 | Ratchet counts by position: a new call above old ones flags an old line | Fixed (M3) — ESLint suppressions count per file and rule |
| B24 | `/* eslint @repo/no-raw-db-client: off */` bypasses `no-dal-disable` | Fixed (M3) — inline config turning the rule off is rejected (`ts-dal-inline-off`) |
| B25 | Claimed: `go mod tidy` drops the ruleguard DSL | Not reproduced: `go-dal` runs `go mod tidy` and ruleguard still fires. The DSL must be added once (`go get .../dsl`); install now says so |
| B26 | `make check` rewrote files (`gofmt -w`); no format check; `new-from-rev` set twice | Fixed (M2) — `go-format`, `test_golangci_config_is_v2` |
| B27 | `mirrors-prettier` archived, pinned to an alpha | Fixed (M2) — maintained mirror; `test_no_archived_hook_repos` |
| B28 | semgrep secret rule fired on tests and fixtures | Fixed (M2) — test paths excluded |
| B29 | `pip install` without `setup-python` | Fixed (M2) — `uvx semgrep@<version>` |
| B30 | `cancel-in-progress` cancelled runs on `main` | Fixed (M2) — `test_main_runs_never_cancelled` |
| B31 | Node variants never checked formatting in CI | Fixed (M2) — `format:check`; `ts-format`, `js-format` |
| B32 | TS/JS variants had no secret scanning | Fixed (M2) — gitleaks job; `ts-secret` |
| B33 | Installed files failed the kit's own Prettier hook | Fixed (M2) — `python-clean`, `test_installable_files_pass_prettier` |
| B34 | On Windows the ratchet read main's baseline from `/tmp` via `node` (`C:\tmp`): main read as 0, so a clean install was red | Fixed (M3) — script deleted; Windows CI runs the ESLint debt cases |
| B35 | `FORCE=1` reinstall deleted whole directories (user hooks, custom rules, the recorded debt baseline) | Fixed (M2) — directories merged, baseline kept |
| B36 | Gitleaks scanned all history on every PR: one old, rotated secret failed every PR forever | Fixed (M2) — PRs scan their own commits; `test_gitleaks_prs_scan_only_their_commits` |
| B37 | On main, "only new issues" compared main with itself (golangci) or full scans failed main on existing debt (semgrep) | Fixed (M2) — main reports debt without failing; `test_main_reports_debt_without_failing` |
| B38 | The pre-commit ruff (pinned v0.8.4) and CI's locked ruff could disagree on formatting | Fixed (M2) — hook runs `uv run ruff`; `test_python_hooks_use_project_ruff` |
| B53 | On Windows (core.autocrlf=true) files check out with CRLF, so Prettier and gofmt fail on a fresh clone | Fixed (M2) — `.gitattributes` forces LF; Windows CI `*-clean` |
| B39 | `jsconfig.json` includes only `src`, `apps`, `packages`; code elsewhere is not type-checked (or TS18003) | Fixed (M3) — checks the whole repo except tooling (`js-types-root`) |
| B40 | Changing modules from a partial set left the npm `check` script stale (CI ran a deleted script or skipped a new check) | Fixed (M3 review) — `test_check_script_follows_every_module_change` |
| B41 | A repo's existing `eslint.config.mjs` / `tsconfig.json` / `ruff.toml` was kept but never wired to the kit's rules, silently | Fixed (M3 review) — install lists them under NOT WIRED with the line to add; `test_existing_config_files_are_kept_and_reported` |
| B42 | `package.json` and Makefile rewritten with CRLF on Windows | Fixed (M3 review) — `test_package_json_written_with_lf` |
| B43 | Python dev tools listed only as optional extras counted as installed; no `uv.lock` created | Fixed (M3 review) — reads the dev group only, runs `uv lock`; `test_dev_dependencies_reads_only_what_uv_sync_installs` |
| B44 | CI assumed npm; pnpm and yarn repos failed | Fixed (M3 review) — `node_package_manager`; `test_package_manager_follows_the_answer` |
| B45 | An existing Makefile's `test`/`check`/`build` targets silently overridden by `hardening.mk` | Fixed (M3 review) — install warns on each clash |
| B46 | ESLint ignored every `*.config.*` file at any depth (e.g. `src/app.config.ts`); an empty poe `check` sequence with no check modules | Fixed (M3 review) — root configs only; no `check` step without modules (`test_no_check_step_without_check_modules`) |
| B48 | Branch protection required CodeQL by default; on a private repo without Code Security it fails every PR and blocks all merges | Fixed (M4 review) — opt-in `require_codeql` |
| B49 | Advice to add a merge queue, but workflows did not run on `merge_group`, so required checks never reported in the queue | Fixed (M4 review) — `test_workflows_run_in_merge_queue` |
| B50 | `protect-branch.sh owner/repo --dry-run` ignored `--dry-run` and applied the change; it silently dropped existing required checks; bare error without `gh` | Fixed (M4 review) — strict argument parsing, `--replace` needed to drop checks; `test_protect_branch_arguments` |
| B51 | AGENTS.md named `check` commands that do not exist when no format/lint/types module is on | Fixed (M4 review) — `test_agents_md_names_only_real_commands` |
| B52 | Protection test compared job ids, not the names GitHub reports, so it could pass for the wrong reason | Fixed (M4 review) — reads `name:` and expands the matrix |
| B47 | A repo that already has a kit-managed file (`.pre-commit-config.yaml`, `.golangci.yml`, ...) makes a non-interactive first install stop with a conflict | Open — documented in the README (install interactively); a pre-flight check is a later improvement |
