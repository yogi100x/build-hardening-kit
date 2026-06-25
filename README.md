# build-hardening-kit

Portable build-quality gates extracted from the SwiftHyre monorepo. Two variants — **`ts/`** (TypeScript) and **`js/`** (plain JavaScript). Everything in **`shared/`** is variant-agnostic.

The goal: make a green build *mean something*. Lint blocks bad patterns, typecheck blocks type bugs (yes, even on JS), a custom plugin blocks project-specific footguns, and a **baseline-ratchet** drives existing debt to zero without blocking new work.

---

## What's in here

```
build-hardening-kit/
  shared/                         # copy into any project, TS or JS
    .husky/pre-commit             # runs lint-staged
    .prettierrc.json              # pinned defaults (version-stable formatting)
    .prettierignore
    .github/workflows/ci.yml      # lint -> typecheck -> ratchet -> env -> test -> build
    .github/scripts/
      check-env-schema.sh         # every process.env.X must be in .env.example
      check-baseline-shrinkage.sh # baseline count may only shrink (the ratchet gate)
    eslint-plugin-template/       # your custom rules live here (plain JS, no build step)
      package.json                # name it @repo/eslint-plugin
      src/index.js                # rule registry
      src/rules/no-raw-db-client.js   # WORKING example rule + baseline-ratchet
      src/baselines/raw-db-from.json  # generated debt snapshot ({} = clean)
      scripts/generate-baseline.mjs   # regenerates the snapshot
  ts/                             # TypeScript variant
    eslint.config.mjs
    tsconfig.json
    package.snippet.json          # merge scripts + lint-staged + devDeps into your package.json
  js/                             # plain-JS variant (uses checkJs for type safety, no .ts files)
    eslint.config.mjs
    jsconfig.json
    package.snippet.json
```

---

## Install (either variant)

1. Copy `shared/` contents into your repo root (merge `.github/`, keep `.husky/`).
2. Copy the chosen variant's `eslint.config.mjs` + `tsconfig.json`/`jsconfig.json` to root.
3. Copy `shared/eslint-plugin-template/` to `packages/eslint-plugin/` (or wherever; update paths in the CI scripts + snippet).
4. Merge `<variant>/package.snippet.json` into your root `package.json` (`scripts`, `lint-staged`, `devDependencies`).
5. `npm install` — the `prepare` script wires Husky automatically.
6. Seed the ratchet: `npm run baseline:generate` then commit the JSON. Now the count can only go down.

Verify: `npm run lint && npm run typecheck`.

---

## TS vs JS — what differs

| Layer | TS variant | JS variant |
|-------|-----------|-----------|
| ESLint base | `@eslint/js` + `typescript-eslint` (type-checked rules) | `@eslint/js` + extra rules TS made redundant (`no-undef`, `no-shadow`, `consistent-return`) |
| Type safety | `tsc --noEmit` on `.ts` | `tsc --noEmit -p jsconfig.json` with `checkJs:true` on `.js` + JSDoc |
| Boundaries | zod/valibot recommended | zod/valibot **strongly** recommended (no compile-time guard at runtime edges) |
| Everything else | identical | identical |

**The JS trick:** you don't have to *write* TypeScript to *use* it. `checkJs:true` + JSDoc types + `tsc --noEmit` recovers ~80% of TS's bug-catching on plain `.js`. The CI `typecheck` job is identical in both — that's why it's not variant-specific.

---

## The baseline-ratchet (the transferable idea)

Most lint rules can't be adopted on a legacy codebase — turning them on floods you with 3000 errors. The ratchet fixes that:

1. `generate-baseline.mjs` snapshots **current** violations per file into `raw-db-from.json`.
2. The ESLint rule only reports violations that **exceed** the snapshot — existing code passes, new violations fail.
3. `check-baseline-shrinkage.sh` (CI) compares the PR's total against `main`'s. It may **shrink or stay flat, never grow**.
4. Fix debt opportunistically; regenerate; the gate locks in the lower number. Debt monotonically decreases to zero.

Opt out per-PR with `[skip-ratchet]` in the PR title/body for unrelated changes.

The example rule targets raw DB-client calls (`supabase.from()`, `db.query()`, `prisma.x`). Rename `no-raw-db-client` and adjust `CLIENT_NAMES` / method list for *your* footgun (raw `fetch`, `console.log`, `dangerouslySetInnerHTML`, deep imports — anything AST-detectable).

> Note: `generate-baseline.mjs` uses a regex for speed (snapshot only); the **rule** uses the AST and is the source of truth. After first generate, run `npm run lint` once — if the AST finds more than the regex seeded, bump the baseline once, commit, then ratchet down.

---

## Notes

- The custom plugin is **plain CommonJS — no build step** (SwiftHyre compiled a TS plugin; this is simpler to port).
- `--max-warnings=0` everywhere: warnings == build failures. That's the lever that keeps the bar from eroding.
- `.prettierrc.json` pins formatting so a Prettier version bump never reformats your whole tree in one PR.
- `check-env-schema.sh` fails the build when code references an env var absent from `.env.example` — catches "works on my machine, undefined in prod".
- No commitlint included (SwiftHyre doesn't enforce it). Add `@commitlint/config-conventional` + a `commit-msg` hook if you want conventional commits.
