# Changelog

The kit follows [semantic versioning](https://semver.org). Install a version
with `uvx copier copy --trust --vcs-ref <tag> ...`; upgrade with
`uvx copier update --trust`.

## 1.0.0 — unreleased

A rewrite. The kit is now a copier template with independent modules and
proves itself with a self-test on Linux, macOS and Windows.

### Added

- Install, upgrade and module changes through copier; presets `minimal` and
  `standard`; modules `format`, `lint`, `types`, `secrets`, `ci`, `hooks`,
  `governance`, `agents`, `arch-rules`.
- One CI workflow running the same entry points as local development
  (`npm run check`, `uv run poe check`, `make check`); npm, pnpm and yarn.
- Branch-protection script requiring exactly the checks the workflows report.
- `AGENTS.md` for coding agents.
- Self-test: fixture repos per stack, upgrade tests, static checks of every
  rendered combination (actionlint, zizmor), nightly runs.

### Changed

- Existing debt is recorded with each tool's own baseline (ESLint bulk
  suppressions, `ruff --add-noqa`, golangci-lint `--new-from-rev`, semgrep
  `--baseline-commit`) instead of the custom ratchet.
- The DAL rule is the optional `arch-rules` module.
- golangci-lint v2; maintained Prettier mirror; gitleaks CLI (no licence key).

### Removed

- `install.sh` and the per-variant folders (use copier).
- `[skip-ratchet]`: no text in a pull request can switch a gate off.
- The bash env-var check (a cross-platform version may return as a module).

### Fixed

59 bugs found by the self-test, independent reviews and a stranger following
only the README. One is open and documented (B47); one reported bug did not
reproduce (B25). See [tests/KNOWN_BUGS.md](tests/KNOWN_BUGS.md).
