# format

**Adds**

| Stack | Files | Command |
|---|---|---|
| TS / JS | `.prettierrc.json` (kit-owned), `.prettierignore` (yours) | `npm run format:check` (CI), `npm run format` (fix) |
| Python | `ruff.hardening.toml` (kit-owned), `ruff.toml` (yours, extends it) | `uv run poe format` (check), `uv run ruff format .` (fix) |
| Go | formatters `gofmt` + `gci` in `.golangci.yml` | `make fmt-check`, `make fmt` (fix) |

**Blocks** any file the formatter would change. Formatting is never discussed
in review again.

**Existing repo.** Run the fix command once and commit the result on its own,
so the reformat is easy to skip in `git blame`
(`git config blame.ignoreRevsFile .git-blame-ignore-revs`).

**Configure.** Prettier: edit `.prettierrc.json` (your edits survive
upgrades). ruff: add settings to `ruff.toml`. gci: the `go_module` answer
groups your own imports last.

**Remove.** Drop `format` from `modules`; the config files and the
`format`/`format:check` npm scripts you did not change are removed.
