# governance

**Adds**

| File | Purpose |
|---|---|
| `.github/CODEOWNERS` | who approves which paths; ships commented out unless you answered `code_owners` (a placeholder owner silently enforces nothing) |
| `.github/dependabot.yml` | weekly grouped updates for your stacks and for GitHub Actions |
| `.github/workflows/codeql.yml` | static analysis for your languages and your workflows |
| `.github/pull_request_template.md` (yours) | what changed, how it was checked, risk and rollback |
| `.github/hardening/protect-branch.sh` | makes exactly the kit's checks block merges ([BRANCH_PROTECTION.md](../BRANCH_PROTECTION.md)) |

With real owners, CODEOWNERS also covers the recorded-debt files
(`eslint-suppressions.json`, `.gitleaksignore`), so growing debt needs an
owner's approval, which GitHub records.

**Answers:** `code_owners` (e.g. `@my-org/maintainers`), `required_reviews`
(default 1; 0 when you work alone), `require_codeql` (default off: on a private
repo without GitHub Code Security the scan fails every pull request, and a
required failing check blocks all merges).

**Process.** [GOOGLE_GRADE.md](../../GOOGLE_GRADE.md) is the human half: what
reviewers look for, small changes, fast reviews.

**Remove.** Drop `governance` from `modules`. Branch protection already
applied on GitHub stays until you change it in Settings > Branches.
