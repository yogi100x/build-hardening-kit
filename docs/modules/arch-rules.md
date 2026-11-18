# arch-rules

An example architecture rule, and the pattern for writing your own: **no raw
database queries outside the data-access layer** (`dal/`, `data-access/` or
`data_access/`). See [DAL_POLICY.md](../../DAL_POLICY.md) for the reasoning.

**Adds**

| Stack | Files | Enforced by |
|---|---|---|
| TS / JS | `tools/hardening/*.mjs`, a local ESLint plugin (needs `lint`) | `@hardening/no-raw-db-client`, `@hardening/no-dal-disable` |
| Python / Go | `.semgrep/hardening.yml` | semgrep (CI job `semgrep`, hook) |
| Go | `hardening_rules.go` (ruleguard, run by golangci-lint's gocritic; holds only the DAL rule — add your own funcs there) | `make lint` |

**Exceptions** must carry a reason on the line above:
`// DAL-EXEMPT: <reason>` then `// eslint-disable-next-line @hardening/no-raw-db-client`.
A disable without a reason, a blanket `eslint-disable`, or inline config that
turns the rule off is itself an error.

**Existing repo.** Record today's raw calls with `npx eslint --suppress-all .`
(TS/JS); semgrep and golangci-lint fail only on new findings in pull requests.

**Write your own rule.** Copy `no-raw-db-client.mjs`, change what it matches
(raw `fetch`, `console.log`, deep imports — anything in the syntax tree), and
register it in `tools/hardening/index.mjs` and `eslint.config.mjs`. For Python
and Go, add a rule to `.semgrep/hardening.yml`.

**Remove.** Drop `arch-rules` from `modules`.
