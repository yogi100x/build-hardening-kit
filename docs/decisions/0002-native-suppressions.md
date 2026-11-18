# 0002 — Record existing debt with each tool's own baseline

**Question.** Strict checks flood an existing repo with findings. How does the
kit let a team adopt them and make debt only go down?

**Chosen.** Each tool's built-in mechanism:

- ESLint bulk suppressions (`eslint --suppress-all`, ESLint 9.24+). A new
  problem fails; fixing a recorded one fails until `--prune-suppressions`
  lowers the count.
- ruff `--add-noqa` for Python.
- `golangci-lint --new-from-rev` and semgrep `--baseline-commit` for issues new
  since the base branch; the default branch reports the rest without failing.

**Why.** The kit's first ratchet was a custom ESLint rule plus a regex baseline
generator plus a shell script. It disagreed with itself (regex vs AST), counted
by position, read the baseline relative to the working directory, failed open
on unreadable files, broke on Windows, and any PR could switch it off by writing
`[skip-ratchet]` in its description. The tools' own baselines have none of
those problems and are maintained upstream.

**Exceptions.** Growing the suppressions file is an explicit, reviewable code
change. With the governance module, CODEOWNERS requires an owner to approve it,
and GitHub records who approved which commit. No PR text can switch a gate off.

**Revisit if** a check the kit adds has no baseline of its own (for example a
bundle-size budget); it then needs a small budget file of its own.
