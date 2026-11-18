# types

**Adds**

| Stack | Files | Command |
|---|---|---|
| TypeScript | `tsconfig.hardening.json` (kit-owned: `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, ...), `tsconfig.json` (yours, extends it) | `npm run typecheck` |
| JavaScript | `jsconfig.hardening.json` (`checkJs` + strict), `jsconfig.json` (yours) | `npm run typecheck` |
| Python | `mypy.ini` (yours: `strict = True`) | `uv run poe types` |
| Go | `go vet` and the compiler | `make check` |

**Blocks** type errors. In JavaScript, `checkJs` with JSDoc types recovers
most of TypeScript's checking without writing TypeScript.

**Existing repo.** Strict settings can produce many errors at once. Turn
single options off in your `tsconfig.json` / `mypy.ini` and back on one at a
time; for mypy, per-module `[mypy-legacy.*]` sections with
`ignore_errors = True` fence old code while new code stays strict.

**Remove.** Drop `types` from `modules`. (TypeScript keeps `tsconfig.*` while
`lint` is on: type-aware lint rules need it.)
