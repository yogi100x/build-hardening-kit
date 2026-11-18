# Branch protection — make the presubmit the arbiter

The linters and CI mean nothing until failing them **blocks merge**. This is the
single highest-leverage Google-grade step: "if it's not green, it can't land."

## One-shot setup (gh CLI)

Replace `OWNER/REPO` and the contexts, then run. Contexts are job names from the
workflows you installed: `quality` and `secrets` (hardening-node), `python`
(hardening-python), `go` (hardening-go), `semgrep` and `secrets`
(hardening-polyglot), `Analyze (<language>)` (CodeQL). Edit `.github/CODEOWNERS`
first: it ships commented out, and `require_code_owner_reviews` with no real
owner enforces nothing.

```bash
OWNER_REPO="your-org/your-repo"

gh api -X PUT "repos/$OWNER_REPO/branches/main/protection" \
  -H "Accept: application/vnd.github+json" \
  --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["quality", "semgrep", "secrets", "Analyze (javascript-typescript)"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "require_code_owner_reviews": true,
    "dismiss_stale_reviews": true
  },
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true,
  "restrictions": null
}
JSON
```

## What each setting enforces

| Setting | Google practice it encodes |
|---------|----------------------------|
| `required_status_checks.strict` | branch must be up-to-date + all checks green before merge (presubmit = arbiter) |
| `contexts` | the exact CI jobs that must pass — use your real job names |
| `require_code_owner_reviews` | an OWNER must approve (`.github/CODEOWNERS`) |
| `required_approving_review_count: 1` | mandatory review — nothing lands unreviewed |
| `dismiss_stale_reviews` | new commits re-trigger review (no rubber-stamp drift) |
| `enforce_admins` | rules apply to everyone, including admins |
| `required_linear_history` | small, clean, revertable history (squash/rebase merges) |
| `required_conversation_resolution` | review comments must be resolved, not ignored |

## Recommended repo settings (UI)

- Settings > General > Pull Requests: enable **"Allow squash merging"** only; **"Automatically delete head branches."** (trunk-based, small CLs)
- Settings > Code security: enable **Dependabot alerts**, **Dependabot security updates**, **Secret scanning**, **Push protection**, **CodeQL**.
- Settings > Branches: set the protection rule on `main` (the API call above does this).
