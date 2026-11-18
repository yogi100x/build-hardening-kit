# 0001 — Distribute the kit as a copier template

**Question.** How does a stranger install the kit, upgrade it later without
losing their own edits, and remove parts of it?

**Chosen.** A [copier](https://copier.readthedocs.io) template. `copier copy`
installs; `copier update` re-renders the new version and merges it with local
edits (three-way); changing `modules` re-renders and deletes files that no
longer apply. The answers live in `.copier-answers.yml`.

**Why.** The original `install.sh` copied files once: every repo drifted from
the kit after day one, a reinstall either skipped files or (with `FORCE=1`)
deleted user directories, and there was no uninstall. A custom installer with
manifests, hashes and three-way merges would rebuild what copier already does.

**Costs.** Users need `uv` (for `uvx copier`) even in a Node-only repo.
Files a template cannot render — `package.json` scripts, Python dev
dependencies, an existing `Makefile` — are wired by a post-install task, so
installing needs `--trust`. The task is short, standard-library-only, and
never overwrites a script the user changed.

**Revisit if** copier's merge proves unreliable in the self-test's upgrade
cases, or a large share of users cannot run `uvx`.
