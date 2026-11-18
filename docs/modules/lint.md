# lint

**Adds**

| Stack | Files | Command |
|---|---|---|
| TS / JS | `eslint.hardening.mjs` (kit-owned), `eslint.config.mjs` (yours, imports it) | `npm run lint` |
| Python | ruff rules in `ruff.hardening.toml` (bugbear, bandit, pyupgrade, ...) | `uv run poe lint` |
| Go | golangci-lint v2 (`.golangci.yml`): staticcheck, gosec, errcheck, errorlint, ... | `make lint` |

**Blocks** likely bugs and unsafe patterns. Warnings count as errors
(`--max-warnings=0`), so the bar cannot slide. TypeScript gets type-aware
rules (floating promises, `any`). Unused `eslint-disable` comments are errors.

**Existing repo — debt only goes down.**

- ESLint: `npx eslint --suppress-all .` records today's problems in
  `eslint-suppressions.json`. A new problem fails. Fixing a recorded one fails
  until `npx eslint --prune-suppressions .` lowers the count. Commit the file;
  with `governance`, an owner must approve it growing.
- ruff: `uv run ruff check --add-noqa .` marks today's findings inline.
- golangci-lint: `make lint` and pull requests fail only on issues new since
  `origin/<default branch>` (with no remote yet, every issue counts as new);
  the default branch reports the rest without failing.

**Notes.** TypeScript tests written with `node:test` pass
`no-floating-promises` (the kit marks `test`/`describe` as awaited by the
runner). revive skips the package-comment rule for `main.go`.

**Configure.** Add rules after the kit's in `eslint.config.mjs`; add or ignore
ruff rules in `ruff.toml`; edit `.golangci.yml`.

**Already had a config?** The kit keeps yours and prints it under
**NOT WIRED** with the line to add (for ESLint: import
`./eslint.hardening.mjs` and spread it first).

**Remove.** Drop `lint` from `modules`.
