# ci

**Adds** `.github/workflows/hardening.yml` (kit-owned) with one job per stack
plus `secrets` and `semgrep` when those modules are on. Each job runs the same
entry point you run locally:

| Job | Runs |
|---|---|
| `node` | install from your lockfile (npm, pnpm or yarn), `npm run check`, `npm test` |
| `python` | `uv sync --locked`, `uv run poe check`, `uv run poe test` |
| `go` | `make check`, `make test` (on the default branch, lint debt is reported, not failed) |

**Security defaults.** Actions pinned to commit SHAs; `permissions: {}` at the
top and read-only per job; checkout without stored credentials; runs on the
default branch are never cancelled. The kit's self-test runs actionlint and
zizmor on representative rendered combinations.

**Requirements.** Node: a `test` script in `package.json`. Python: a committed
`uv.lock`. Go: `go.mod`.

**Make it block merges** with the `governance` module's
`.github/hardening/protect-branch.sh`.

**Not GitHub?** Every job is one or two commands; copy them into your CI.

**Remove.** Drop `ci` from `modules`.
