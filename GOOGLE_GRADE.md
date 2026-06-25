# Google-Grade Engineering

The `ts/js/go/python/polyglot` kits are the **automatable presubmit** half. This file is the **human + process** half — distilled from Google's published practices. Tooling stops bad syntax; process stops bad *changes*. You need both.

Sources (read them — short): [google/eng-practices](https://github.com/google/eng-practices) (CC-BY 3.0), [google/styleguide](https://github.com/google/styleguide), [Software Engineering at Google](https://abseil.io/resources/swe-book) (free).

---

## 1. The one rule that matters most (Standard of Code Review)

> **Approve a CL once it definitely improves the overall code health of the system — even if it isn't perfect.**

- There is no "perfect" code, only *better* code. Seek **continuous improvement**, not perfection.
- Never block forward progress for days over polish. Prefix optional polish with **`Nit:`** — author may ignore.
- Never approve a CL that *worsens* code health (except a real [emergency](https://github.com/google/eng-practices/blob/master/review/emergencies.md)).
- Reviewer has ownership: keep the codebase consistent and maintainable over time.

## 2. What a reviewer looks for (in priority order)

[Full list](https://github.com/google/eng-practices/blob/master/review/reviewer/looking-for.md). Top to bottom:

1. **Design** — most important. Do the pieces interact sensibly? Does this belong here vs a library? Is now the right time?
2. **Functionality** — does it do what was intended; edge cases; concurrency (deadlocks/races read, not just run).
3. **Complexity** — "can't be understood quickly by readers" = too complex. **Watch for over-engineering** — solve the problem you have *now*, not a speculated future one.
4. **Tests** — ask for tests with the code change, in the same CL. Tests must actually fail when the code breaks.
5. **Naming** — clear, not too long/short.
6. **Comments** — explain **WHY**, not WHAT. (Enforced in-code by the `// WHY:`/`DAL-EXEMPT:` rules.)
7. **Style / consistency** — from the language style guide. `Nit:` if minor. Style is automated (formatter) so review spends zero time here.
8. **Documentation** — update READMEs/docs when behavior changes.
9. **Every line** — the reviewer actually read every human-written line (generated/data files exempted).

## 3. Small CLs (author discipline)

[Why](https://github.com/google/eng-practices/blob/master/review/developer/small-cls.md): small changes are reviewed faster + more thoroughly, introduce fewer bugs, waste less work if rejected, roll back cleanly.

- **One self-contained change = one CL.** Usually *part* of a feature, not a whole feature.
- Reviewers may **reject a CL outright for being too large.** Err small.
- Include the related tests in the same CL.
- Big mechanical change? Split: one CL for the refactor, separate CLs for behavior.

## 4. CL / commit descriptions

[Guide](https://github.com/google/eng-practices/blob/master/review/developer/cl-descriptions.md). The description is a permanent record read by people years later.

- **First line:** short imperative summary ("Delete the FizzBuzz RPC", not "Deleting…"). Stands alone. Blank line after.
- **Body:** *what* + *why*. Capture decisions and context not visible in the code (Chesterton's fence).
- Bad: `"fix bug"`, `"update"`, `"wip"`. Good: states the problem and the approach.

## 5. Review speed

[Guide](https://github.com/google/eng-practices/blob/master/review/reviewer/speed.md). Optimize team velocity, not individual velocity.

- **Respond within one business day** (max). A CL should get multiple review rounds in a day.
- Don't interrupt your own focused work to review — do it at a breakpoint.
- Most complaints about "strict" reviewers actually vanish when reviews are **fast**.

## 6. Principles from *Software Engineering at Google*

- **"Software engineering is programming integrated over time."** Optimize for the code's whole lifetime, not today.
- **Code is a liability, not an asset.** The best CL is often a *deletion*. Less code = less to maintain.
- **Hyrum's Law** — with enough users, every observable behavior of your system will be depended on. Don't expose what you don't intend to support.
- **The Beyoncé Rule** — "if you liked it, you shoulda put a test on it." If you don't want it to break, **CI must check it.** An untested invariant is a broken invariant waiting to happen.
- **Single source of truth + presubmit gate.** The build/test system is the arbiter — not opinions. "If it's not tested, it's broken."
- **Tests:** prefer many small/fast tests; test **behaviors, not methods**; in test code prefer **DAMP over DRY** (readable beats clever).
- **Design for change** — "nothing is built on stone." Automate large-scale changes (LSC) rather than hand-editing.
- **Trade-offs over rules** — "it depends." Document the reasoning; don't cargo-cult.
- **Scale question** — "what happens if this is done 1000× / by 1000 engineers?" If it degrades, fix the process not the instance.

## 7. How the kit enforces this automatically

| Google practice | Kit mechanism |
|-----------------|---------------|
| Style not discussed in review | auto-formatter (prettier/gofmt/ruff) + `--max-warnings=0` |
| Comments explain WHY | `any-requires-justification`, `DAL-EXEMPT:` rules |
| Every invariant tested (Beyoncé) | CI test job + coverage gate |
| Presubmit is the arbiter | required status checks (see `docs/BRANCH_PROTECTION.md`) |
| Reviewed by an owner | `.github/CODEOWNERS` + required-review branch protection |
| Vetted dependencies | `.github/dependabot.yml` + secret/SAST scans |
| Centralized data access | DAL rules (`DAL_POLICY.md`) |
| Small CLs / good descriptions | process — enforce in review (optionally a CL-size CI warning) |

## 8. Adopting the style guides

[google/styleguide](https://github.com/google/styleguide) is the source for `gofmt` (Go), `google-java-format`, `clang-format` (C++), and the Python/TS/Shell guides. For TS/JS, the kit's strict ESLint config already encodes most of it; read the [TS style guide](https://google.github.io/styleguide/tsguide.html) for the rest. (Note: the old `eslint-config-google` npm package is unmaintained — don't depend on it; use the kit config + the guide.)
