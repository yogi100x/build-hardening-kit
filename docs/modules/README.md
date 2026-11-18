# Modules

Each module is independent. Add or remove one with
`uvx copier update --trust --data 'modules=[...]'` (list every module you want
to keep). Each page says what the module adds, what it blocks, how to adopt it
on a repository that already has problems, and how to remove it.

| Module | Preset | Page |
|---|---|---|
| `format` | minimal | [format.md](format.md) |
| `lint` | minimal | [lint.md](lint.md) |
| `types` | minimal | [types.md](types.md) |
| `secrets` | minimal | [secrets.md](secrets.md) |
| `ci` | minimal | [ci.md](ci.md) |
| `hooks` | standard | [hooks.md](hooks.md) |
| `governance` | standard | [governance.md](governance.md) |
| `agents` | standard | [agents.md](agents.md) |
| `arch-rules` | off | [arch-rules.md](arch-rules.md) |

"Kit-owned" files are kept current by `copier update` (your edits to them are
merged). "Yours" files are created once and never overwritten.
