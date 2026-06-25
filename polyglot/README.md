# Polyglot build hardening (Go, Python, and beyond)

The same four gates from the JS/TS kit — **format → lint → type/compile → custom-rule ratchet**, plus secrets — generalize to any language. You don't build a bespoke kit per language; you keep **three universal tools** and swap only the per-language formatter/linter/typechecker.

## The three universal tools

| Tool | Role | Replaces (from JS/TS kit) |
|------|------|---------------------------|
| **pre-commit** (`.pre-commit-config.yaml`) | language-agnostic git-hook runner | Husky + lint-staged |
| **semgrep** (`semgrep/rules.yml`) | custom AST rules in ONE file across all langs, with `--baseline-commit` ratchet | the custom ESLint plugin + baseline JSON |
| **gitleaks** (`.gitleaks.toml`) | secret scanning, language-agnostic | (new — add to every project) |

## Per-language swap-ins

| Layer | JS/TS | Go | Python | Rust | "Others" |
|-------|-------|----|--------|------|---------|
| Format | prettier | `gofmt`/`gofumpt` | `ruff format` | `rustfmt` | `shfmt`, `terraform fmt` |
| Lint | eslint | **golangci-lint** (50+ linters) | **ruff** | `clippy -D warnings` | `shellcheck`, `hadolint`, `yamllint` |
| Type/compile | `tsc` / `checkJs` | compiler | **mypy --strict** | compiler | — |
| Custom rules | eslint plugin | ruleguard (`rules.go`) | semgrep | dylint | **semgrep** (all) |
| Ratchet | baseline JSON | golangci `--new-from-rev` | semgrep `--baseline-commit` | — | semgrep baseline |
| Test gate | vitest/jest | `go test -race` | `pytest` | `cargo test` | — |

**Key insight:** every language already ships a strong meta-linter (golangci-lint, ruff, clippy) and a built-in ratchet (`--new-from-rev`, `--baseline-commit`). So the polyglot kit is *smaller* than the JS one — you mostly wire existing tools, not write rules.

## What's here

```
polyglot/
  .pre-commit-config.yaml   # one hook runner for every language (incl. shell, Dockerfile)
  semgrep/rules.yml         # custom rules: matches Go + Python + JS/TS + more at once
  .gitleaks.toml            # secret scanning config
  ci.yml                    # universal semgrep+secrets jobs; paste per-lang jobs in
../go/                      # .golangci.yml, rules.go (ruleguard), Makefile + CI snippets
../python/                  # ruff + mypy config, CI snippet
```

## Install

1. `pipx install pre-commit && pre-commit install` (root). Now every commit runs the configured linters/formatters/secret-scan for whatever files changed.
2. Drop `.golangci.yml`+`rules.go` (Go) and `pyproject.snippet.toml` (Python) into the relevant subprojects.
3. Copy `polyglot/ci.yml` to `.github/workflows/` and paste the `go:`/`python:` jobs from each `ci.snippet.yml`.
4. Seed the ratchet implicitly: `--new-from-rev=origin/main` and `--baseline-commit` use git history — nothing to commit; existing debt is grandfathered, new debt fails.

## Adding more languages

- **Rust:** `rustfmt`, `clippy -D warnings`, `cargo test`; add a `clippy` hook to pre-commit, a `rust` job to CI.
- **Java/Kotlin:** `spotless` (format) + `errorprone`/`detekt` (lint); semgrep already covers custom rules.
- **Terraform:** `terraform fmt -check`, `tflint`, `tfsec`.
- **Shell / Dockerfile / YAML:** already wired in `.pre-commit-config.yaml` (shellcheck, hadolint, check-yaml).

In all cases: add the formatter+linter hook to pre-commit, the test/build to CI, and lean on **semgrep + gitleaks** — unchanged — for custom rules and secrets.
