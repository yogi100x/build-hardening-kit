# DAL Policy — no raw queries

**Rule: every database query lives in the data-access layer (`dal/`). Application code never touches the DB client directly.**

Why: one place to enforce access control, caching, query shape, and auditing. Raw queries scattered across the app are impossible to secure or optimize and are the #1 source of N+1 and RLS-bypass bugs.

## What's blocked

Outside any `dal/`, `data-access/` or `data_access/` directory, these fail the build:

```ts
const rows = await db.query("select * from users")       // ❌
const { data } = await supabase.from("users").select()    // ❌
await prisma.user.findMany()                              // ❌ (any call on prisma, JS/TS only)
```

Move them into a DAL function:

```ts
// dal/users/index.ts
export async function listUsers() {        // ✅
  const { data } = await supabase.from("users").select();
  return data;
}
// app code:
import { listUsers } from "@/dal/users";
const users = await listUsers();           // ✅
```

## How it's enforced (per stack)

| Stack | Enforced by |
|-------|-------------|
| JS / TS | ESLint rule `@repo/no-raw-db-client` (baseline-ratcheted) + `@repo/no-dal-disable` (can't silently disable it) |
| Go | ruleguard `rawDBQuery` in `rules.go` (via golangci-lint) |
| Python / any | semgrep rule `no-raw-db-query-outside-dal` |

## Adapting to your client

- **JS/TS:** edit `CLIENT_NAMES` + `METHODS` in `packages/eslint-plugin/src/rules/no-raw-db-client.js`.
- **Go:** edit the match patterns + `PkgPath` regex in `rules.go`.
- **semgrep:** edit `patterns` + `paths.exclude` in `semgrep/rules.yml`.

Default client names matched: `supabase`, `client`, `db`, `adminClient`, `prisma`, `knex`.
Default DAL paths (exempt): anything under `dal/`, `data-access/` or `data_access/` (ESLint rule, semgrep rule and baseline generator use the same list). The Go ruleguard rule exempts packages whose import path ends in `/dal`.

## Escape hatch (rare, must be justified)

A genuinely necessary raw query outside the DAL must be explicit:

```ts
// DAL-EXEMPT: one-off migration backfill, not part of request path
// eslint-disable-next-line @repo/no-raw-db-client
const rows = await db.query(sql);
```

A bare `eslint-disable` or a disable without a `DAL-EXEMPT:` reason is itself a lint error (`@repo/no-dal-disable`). The baseline-ratchet grandfathers existing raw queries and blocks new ones — drive the count to zero over time.
