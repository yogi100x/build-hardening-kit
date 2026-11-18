# Branch protection — make the checks block merges

Linters and CI mean nothing until a failing check **blocks merging**. Hooks on a
developer's machine can always be skipped; branch protection cannot.

## With the `governance` module (recommended)

The kit renders `.github/hardening/protect-branch.sh`. It requires exactly the
checks your workflows really run — a required check that never reports would
block every merge — and `copier update` keeps that list current when you add or
remove stacks and modules.

```bash
.github/hardening/protect-branch.sh --dry-run   # show the settings, change nothing
.github/hardening/protect-branch.sh             # apply to this repo's default branch
```

The call replaces the branch's whole protection. If required checks are set
today that are not the kit's, the script stops and lists them; re-run with
`--replace` to drop them, or add them back by hand afterwards.

CodeQL is not a required check unless you answered `require_codeql: true`.
CodeQL is free on public repos; on a private repo without GitHub Code Security
the scan fails on every pull request, and a required failing check blocks all
merges.

Needs the GitHub CLI (`gh`) signed in with admin rights on the repo. Branch
protection on a private repo needs a paid GitHub plan; public repos are free.

| Setting | Why |
|---|---|
| required status checks | every kit job must pass (and each CodeQL language, if `require_codeql`) |
| `strict: false` | a branch need not be rebased on the latest base first; turn it on, or add a merge queue (the kit's workflows run on `merge_group`), once "green on my branch, red on main" happens often |
| `enforce_admins` | the rules apply to admins too |
| approving reviews | `required_reviews` (default 1). Working alone? Set it to 0: GitHub does not let you approve your own pull request |
| code-owner review | only when you named real owners (`code_owners`); a placeholder owner silently enforces nothing |
| `dismiss_stale_reviews` | new commits need a fresh approval |
| conversation resolution | review comments must be resolved |
| no force pushes, no deletion | history on the default branch is permanent |

Change `required_reviews` or `code_owners` with
`uvx copier update --trust --data required_reviews=0`, then run the script again.

## Recommended repository settings

- Settings > General > Pull Requests: allow squash merging; automatically delete head branches.
- Settings > Code security: Dependabot alerts and security updates, secret
  scanning, push protection, CodeQL.
- To block merges on CodeQL *findings* (not only on the scan running), add a
  code-scanning merge protection rule under Settings > Rules.
