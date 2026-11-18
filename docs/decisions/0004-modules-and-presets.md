# 0004 — Independent modules with presets

**Question.** How is the kit cut so a stranger takes only what fits?

**Chosen.** Independent modules (`format`, `lint`, `types`, `secrets`, `ci`,
`hooks`, `governance`, `agents`, `arch-rules`) and two presets that are only
module lists: `minimal` and `standard`. Any module can be added or removed
later with `copier update --data 'modules=[...]'`.

**Why.** Ordered levels ("you are at level 2") imply everyone climbs the same
ladder, but a Go CLI never wants page-speed checks and a library may want
signed releases without a deploy step. Presets are what people pick; modules
are what they trim.

**Not in v1.** A tests module (no-network guard, `TZ=UTC`, flaky-test
quarantine), code-health checks (dead code, duplication, bundle budgets),
supply-chain extras (SBOM, signed releases), Rust, and non-GitHub CI wrappers.
Each arrives as its own module, proved by the same self-test.
