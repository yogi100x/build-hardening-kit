# hooks

**Adds** `.pre-commit-config.yaml` (kit-owned): whitespace and merge-conflict
checks, YAML/JSON validity, Prettier (your locked version), ruff (your locked
version, via `uv run`), golangci-lint, shellcheck, gitleaks on staged changes,
and the semgrep rules when `arch-rules` is on.

**Install once per clone:** `uvx pre-commit install`.

**Hooks are feedback, not enforcement.** Anyone can skip them with
`--no-verify`, so the CI workflow is the real gate. Hooks just tell you sooner.

**Already had a `.pre-commit-config.yaml`?** copier asks before replacing it on
the first install; keep yours and copy in the hooks you want, or move yours
aside and merge it back afterwards.

**Remove.** Drop `hooks` from `modules`, then `uvx pre-commit uninstall`.
