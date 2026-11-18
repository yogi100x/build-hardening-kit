# agents

**Adds** `AGENTS.md` (yours) and `CLAUDE.md` (yours, one line: `@AGENTS.md`).

`AGENTS.md` is read by most coding agents (Codex, Cursor, Copilot, Gemini and
others); Claude Code reads `CLAUDE.md`, which imports it. It lists the gate
commands for your stacks and the rules that matter to an agent: run the gate
before saying a change is done, never skip hooks or disable a check, never
grow the suppressions file to hide a problem, never commit a secret, keep
database calls in the data-access layer.

Edit it freely: add your project's own commands and rules. It is created once
and never overwritten.

**Remove.** Drop `agents` from `modules` (your edited files stay; delete them
if you no longer want them).
