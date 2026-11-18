# 0003 — Render the CI workflow into the repo

**Question.** Should repos call reusable workflows hosted in the kit's
repository (`uses: <kit>/.github/workflows/node.yml@<sha>`) or carry their own?

**Chosen.** The kit renders one workflow, `.github/workflows/hardening.yml`,
into the repo. Each job runs the same local entry point a developer runs
(`npm run check`, `uv run poe check`, `make check`). `copier update` keeps it
current.

**Why.** The benefit of reusable workflows — a fix made once reaches every
repo — already comes from `copier update`. Rendering avoids making every user's
CI depend on another repository at run time, keeps the whole gate readable in
the user's own repo, works on forks and GitHub Enterprise without cross-repo
access settings, and keeps each job equal to the local command.

**Revisit if** users ask to receive CI fixes without running `copier update`,
or need one central workflow across many repositories in an organisation.
