# secrets

**Adds** `.gitleaks.toml` (yours; extends gitleaks' default rules) and, with
`ci`, a `secrets` job running the gitleaks CLI image pinned by digest (no
licence key). With `hooks`, the gitleaks hook scans what you are about to
commit.

**Blocks** committed credentials: API keys, tokens, private keys, connection
strings. Pull requests scan only their own commits; the default branch scans
the whole history.

**A secret was found.** Rotate it first — it is exposed the moment it was
pushed — then remove it from the code. A finding that is not a secret (a test
fixture, an example) goes in `.gitleaksignore` (one fingerprint per line,
printed in the report). With `governance`, an owner approves that file.

**Also turn on** GitHub secret scanning and push protection (Settings > Code
security): they stop many secrets before they reach the repository at all.

**Remove.** Drop `secrets` from `modules`.
