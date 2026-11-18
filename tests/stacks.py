"""What each stack installs, how it is set up, and which commands are its gate.

The gate follows what the kit documents and its CI workflow runs, so the
self-test checks exactly what a user gets.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field

from harness import IS_WINDOWS, KIT, Repo, run, tool

Step = Callable[[Repo], None]
# (label, argv, cwd relative to repo root). Labels starting with "entry:" are the
# documented entry points (npm run check, uv run poe check, make check): they run
# on the clean repo only; planted cases target the individual steps.
GateStep = tuple[str, list[str], str]

ALL_MODULES = ["format", "lint", "types", "secrets", "ci", "hooks", "governance", "arch-rules"]


def copier_copy(stacks: list[str], modules: list[str] | None = None, **data: str) -> Step:
    """Install the kit the documented way: copier copy --trust."""

    def step(repo: Repo) -> None:
        args = ["--data", f"stacks={json.dumps(stacks)}"]
        args += ["--data", f"modules={json.dumps(modules or ALL_MODULES)}"]
        for key, value in data.items():
            args += ["--data", f"{key}={value}"]
        res = run(
            [
                *tool("copier"),
                "copy",
                "--trust",
                "--defaults",
                "--vcs-ref",
                "HEAD",
                *args,
                str(KIT),
                str(repo.path),
            ],
            repo.path,
            timeout=1200,
        )
        if not res.ok:
            raise RuntimeError(f"copier copy failed:\n{res.out}")

    return step


def write(files: dict[str, str]) -> Step:
    def step(repo: Repo) -> None:
        for rel, content in files.items():
            repo.write(rel, content)

    return step


def cmd(*argv: str, cwd: str = "") -> Step:
    def step(repo: Repo) -> None:
        exe = tool(argv[0])
        res = run([*exe, *argv[1:]], repo.path / cwd if cwd else repo.path)
        if not res.ok:
            raise RuntimeError(f"{' '.join(argv)} failed:\n{res.out}")

    return step


@dataclass
class Case:
    """A change planted on a `pr` branch and what the gate must do with it."""

    files: dict[str, str]
    # Gate step labels that should react. Only steps green on the clean repo count.
    steps: set[str]
    # Regex that must appear in a failing step's output, so a crash or an
    # unrelated rule never counts as "caught". Unused when must_pass is set.
    expect: str = ""
    env: dict[str, str] = field(default_factory=dict)
    # True: a legitimate change the gate must accept (e.g. debt going down).
    must_pass: bool = False


@dataclass
class Stack:
    fixture: str
    setup: list[Step]
    gate: list[GateStep]
    tools: list[str]
    cases: dict[str, Case] = field(default_factory=dict)


SECRET_LINE = 'AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYzXq9Lr4Tq2"\n'
GITLEAKS_FAILED = r"leaks found"
RAW_DB_DECL = "declare const db: { query(sql: string): Promise<unknown> };\n"


def legacy(calls: int) -> str:
    """A file with recorded architecture debt: `calls` raw DB calls."""
    body = "".join(f'export const q{i} = db.query("select {i}");\n' for i in range(calls))
    return RAW_DB_DECL + body


def suppressions(calls: int) -> str:
    data = {"src/legacy.ts": {"@hardening/no-raw-db-client": {"count": calls}}}
    return json.dumps(data, indent=2)


C = Case

TS_CASES = {
    "lint": C(
        {
            "src/bad_lint.ts": "export function same(a: number, b: number): boolean {\n  return a == b;\n}\n"
        },
        {"lint"},
        r"eqeqeq",
    ),
    "types": C(
        {"src/bad_types.ts": 'export const count: number = "three";\n'}, {"typecheck"}, r"TS2322"
    ),
    "format": C({"src/bad_format.ts": "export const   spaced =1\n"}, {"format"}, r"bad_format"),
    "dal": C(
        {"src/bad_dal.ts": RAW_DB_DECL + 'export const rows = db.query("select 1");\n'},
        {"lint"},
        r"no-raw-db-client",
    ),
    "dal-prisma": C(
        {
            "src/bad_prisma.ts": (
                "declare const prisma: { user: { findMany(): Promise<unknown> } };\n"
                "export const users = prisma.user.findMany();\n"
            )
        },
        {"lint"},
        r"no-raw-db-client",
    ),
    # Every DAL directory spelling the policy names is exempt.
    "dal-dir-exempt": C(
        {"src/data_access/users.ts": RAW_DB_DECL + 'export const rows = db.query("select 1");\n'},
        {"lint"},
        must_pass=True,
    ),
    # B24: inline config may not switch the DAL rule off.
    "dal-inline-off": C(
        {
            "src/bad_inline.ts": (
                "/* eslint @hardening/no-raw-db-client: off */\n"
                + RAW_DB_DECL
                + 'export const rows = db.query("select 1");\n'
            )
        },
        {"lint"},
        r"Inline config may not turn",
    ),
    # Debt recorded on main (2 raw calls in src/legacy.ts) may only go down.
    "debt-grow": C({"src/legacy.ts": legacy(3)}, {"lint"}, r"no-raw-db-client"),
    "debt-shrink-unrecorded": C(
        {"src/legacy.ts": legacy(1)}, {"lint"}, r"suppressions left that do not occur"
    ),
    "debt-shrink": C(
        {"src/legacy.ts": legacy(1), "eslint-suppressions.json": suppressions(1)},
        {"lint"},
        must_pass=True,
    ),
    # B01: no text in a PR can switch a gate off.
    "debt-bypass": C(
        {"src/legacy.ts": legacy(3)},
        {"lint"},
        r"no-raw-db-client",
        env={"PR_BODY": "[skip-ratchet]", "PR_TITLE": "[skip-ratchet]"},
    ),
    "secret": C({"src/bad_secret.ts": "export const " + SECRET_LINE}, {"secrets"}, GITLEAKS_FAILED),
    "test": C(
        {
            "test/bad.test.mjs": (
                'import { test } from "node:test";\nimport assert from "node:assert/strict";\n\n'
                'test("planted", () => {\n  assert.equal(1, 2);\n});\n'
            )
        },
        {"test"},
        r"planted",
    ),
}

JS_CASES = {
    "lint": C(
        {"src/bad_lint.js": "export function same(a, b) {\n  return a == b;\n}\n"},
        {"lint"},
        r"eqeqeq",
    ),
    "types": C(
        {"src/bad_types.js": '/** @type {number} */\nexport const count = "three";\n'},
        {"typecheck"},
        r"TS2322",
    ),
    # B39: code outside src/ is type-checked too.
    "types-root": C(
        {"lib/bad_types.js": '/** @type {number} */\nexport const count = "three";\n'},
        {"typecheck"},
        r"TS2322",
    ),
    "format": C({"src/bad_format.js": "export const   spaced =1\n"}, {"format"}, r"bad_format"),
    "dal": C(
        {
            "src/bad_dal.js": (
                "const db = { query: async (/** @type {string} */ s) => s };\n"
                'export const rows = db.query("select 1");\n'
            )
        },
        {"lint"},
        r"no-raw-db-client",
    ),
    "secret": C({"src/bad_secret.js": "export const " + SECRET_LINE}, {"secrets"}, GITLEAKS_FAILED),
}

PY_CASES = {
    "lint": C({"src/app/bad_lint.py": "import os\n"}, {"lint"}, r"F401"),
    "types": C(
        {"src/app/bad_types.py": 'count: int = "three"\n'}, {"types"}, r"Incompatible types"
    ),
    "format": C({"src/app/bad_format.py": "x=1\n"}, {"format"}, r"bad_format"),
    "test": C(
        {"tests/test_bad.py": "def test_fails() -> None:\n    assert 1 == 2\n"},
        {"test"},
        r"test_fails",
    ),
    "dal": C(
        {
            "src/app/bad_dal.py": (
                "from typing import Any\n\n\ndef rows(db: Any) -> Any:\n"
                '    return db.execute("select 1")\n'
            )
        },
        {"semgrep"},
        r"no-raw-db-query-outside-dal",
    ),
    "secret": C({"src/app/bad_secret.py": SECRET_LINE}, {"secrets"}, GITLEAKS_FAILED),
}

GO_CASES = {
    "lint": C(
        {"bad_lint.go": 'package main\n\nimport "os"\n\nfunc cleanup() {\n\tos.Remove("x")\n}\n'},
        {"lint"},
        r"errcheck",
    ),
    "types": C(
        {"bad_types.go": 'package main\n\nvar count int = "three"\n'}, {"build"}, r"cannot use"
    ),
    "format": C(
        {"bad_format.go": "package main\n\nvar   spaced=1\n"}, {"format"}, r"bad_format\.go"
    ),
    "test": C(
        {
            "bad_test.go": (
                'package main\n\nimport "testing"\n\n'
                'func TestFails(t *testing.T) { t.Fatal("planted") }\n'
            )
        },
        {"test"},
        r"TestFails",
    ),
    "dal": C(
        {
            "bad_dal.go": (
                'package main\n\nimport "database/sql"\n\n'
                'func rows(db *sql.DB) error {\n\t_, err := db.Query("select 1")\n\treturn err\n}\n'
            )
        },
        {"lint", "semgrep"},
        r"raw DB query outside dal|no-raw-db-query-outside-dal",
    ),
    "secret": C(
        {"bad_secret.go": "package main\n\n// " + SECRET_LINE}, {"secrets"}, GITLEAKS_FAILED
    ),
}

NPM_INSTALL = cmd("npm", "install", "--no-audit", "--no-fund")
SECRETS: GateStep = (
    "secrets",
    ["gitleaks", "git", "--no-banner", "--redact", "--config", ".gitleaks.toml", "."],
    "",
)
SEMGREP: GateStep = (
    "semgrep",
    ["semgrep", "scan", "--config", ".semgrep/hardening.yml", "--error", "--metrics", "off"],
    "",
)
HOOKS: GateStep = (
    "hooks",
    ["pre-commit", "run", "--all-files", "--show-diff-on-failure"],
    "",
)


def node_gate() -> list[GateStep]:
    """The steps hardening.yml's node job runs (via npm run check), one by one."""
    return [
        ("entry:check", ["npm", "run", "check"], ""),
        ("format", ["npm", "run", "format:check"], ""),
        ("lint", ["npm", "run", "lint"], ""),
        ("typecheck", ["npm", "run", "typecheck"], ""),
        ("test", ["npm", "test"], ""),
        SECRETS,
        HOOKS,
    ]


def py_gate() -> list[GateStep]:
    return [
        # hardening.yml installs with --locked: a stale uv.lock fails.
        ("deps", ["uv", "sync", "--locked", "--quiet"], ""),
        ("entry:check", ["uv", "run", "poe", "check"], ""),
        ("format", ["uv", "run", "ruff", "format", "--check", "."], ""),
        ("lint", ["uv", "run", "ruff", "check", "."], ""),
        ("types", ["uv", "run", "mypy", "."], ""),
        ("test", ["uv", "run", "poe", "test"], ""),
    ]


# The mono repo's single workflow must carry a job for each stack.
CI_HAS_BOTH = (
    "import pathlib, sys; t = pathlib.Path('.github/workflows/hardening.yml').read_text(); "
    "sys.exit(0 if '\\n  node:' in t and '\\n  python:' in t else 1)"
)

TS_SETUP_DEBT = [
    write({"src/legacy.ts": legacy(2)}),
    cmd("npx", "eslint", "--suppress-all", "."),
]

STACKS: dict[str, Stack] = {
    "ts": Stack(
        fixture="ts",
        setup=[copier_copy(["ts"], code_owners="@example/maintainers"), *TS_SETUP_DEBT],
        gate=node_gate(),
        tools=["node", "npm", "npx", "gitleaks", "copier", "pre-commit"],
        cases=TS_CASES,
    ),
    "js": Stack(
        fixture="js",
        setup=[copier_copy(["js"])],
        gate=node_gate(),
        tools=["node", "npm", "gitleaks", "copier", "pre-commit"],
        cases=JS_CASES,
    ),
    "python": Stack(
        fixture="python",
        setup=[copier_copy(["python"])],
        gate=[*py_gate(), SEMGREP, SECRETS, HOOKS],
        tools=["uv", "git", "gitleaks", "copier", "pre-commit", "semgrep"],
        cases=PY_CASES,
    ),
    "go": Stack(
        fixture="go",
        setup=[copier_copy(["go"], go_module="example.com/fixture"), cmd("go", "mod", "tidy")],
        gate=[
            # make is not on Windows runners; the steps below cover the same checks.
            *([] if IS_WINDOWS else [("entry:check", ["make", "check"], "")]),
            ("build", ["go", "build", "./..."], ""),
            ("vet", ["go", "vet", "./..."], ""),
            ("test", ["go", "test", "./..."], ""),
            ("format", ["golangci-lint", "fmt", "--diff"], ""),
            ("lint", ["golangci-lint", "run", "--new-from-rev=origin/main"], ""),
            SEMGREP,
            SECRETS,
            HOOKS,
        ],
        tools=[
            "go",
            "golangci-lint",
            *([] if IS_WINDOWS else ["make"]),
            "git",
            "gitleaks",
            "copier",
            "pre-commit",
            "semgrep",
        ],
        cases=GO_CASES,
    ),
    # A TS web app and a Python service in one repo, installed together.
    "mono": Stack(
        fixture="mono",
        setup=[copier_copy(["ts", "python"], modules=["format", "lint", "types", "secrets", "ci"])],
        gate=[
            *[s for s in node_gate() if s[0] not in {"entry:check", "hooks"}],
            *[s for s in py_gate() if s[0] != "entry:check"],
            ("ci-has-both", [sys.executable, "-c", CI_HAS_BOTH], ""),
        ],
        tools=["node", "npm", "uv", "gitleaks", "copier"],
        cases={
            "ts-lint": TS_CASES["lint"],
            "py-lint": C({"services/api/bad_lint.py": "import os\n"}, {"lint"}, r"F401"),
        },
    ),
}


def run_gate(
    stack: Stack, repo: Repo, only: set[str] | None = None, env: dict[str, str] | None = None
) -> dict[str, str]:
    """Run gate steps: all (clean run), or only those labelled in `only`.

    Returns {label: output tail} for each step that failed.
    """
    failures = {}
    for label, argv, cwd in stack.gate:
        if only is not None and label not in only:
            continue
        exe = tool(argv[0])
        res = run([*exe, *argv[1:]], repo.path / cwd if cwd else repo.path, env=env)
        if not res.ok:
            failures[label] = res.out[-6000:]
    return failures


def caught(case: Case, failures: dict[str, str]) -> bool:
    return any(re.search(case.expect, out) for out in failures.values())
