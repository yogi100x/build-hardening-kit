"""What each stack installs, how it is set up, and which commands are its gate.

This table follows the kit's own documentation (README, install.sh NEXT lines,
CI snippets) so the self-test checks what a user following the docs gets.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field

from harness import KIT, Repo, bash, run, tool

Step = Callable[[Repo], None]
GateStep = tuple[str, list[str], str]  # (label, argv, cwd relative to repo root)


def install(variant: str, subdir: str = "") -> Step:
    def step(repo: Repo) -> None:
        target = repo.path / subdir if subdir else repo.path
        res = run([*bash(), str(KIT / "install.sh"), variant, str(target)], repo.path)
        if not res.ok:
            raise RuntimeError(f"install.sh {variant} failed:\n{res.out}")

    return step


def merge_package_snippet(subdir: str = "") -> Step:
    """README step 4: merge package.snippet.json into package.json."""

    def step(repo: Repo) -> None:
        root = repo.path / subdir if subdir else repo.path
        pkg_path, snip_path = root / "package.json", root / "package.snippet.json"
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        snip = json.loads(snip_path.read_text(encoding="utf-8"))
        for key in ("scripts", "devDependencies"):
            pkg[key] = {**pkg.get(key, {}), **snip.get(key, {})}
        pkg["lint-staged"] = snip.get("lint-staged", {})
        pkg_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
        snip_path.unlink()

    return step


def append_pyproject_snippet(subdir: str = "") -> Step:
    """install.sh NEXT: merge pyproject.snippet.toml into pyproject.toml."""

    def step(repo: Repo) -> None:
        root = repo.path / subdir if subdir else repo.path
        snip = root / "pyproject.snippet.toml"
        with (root / "pyproject.toml").open("a", encoding="utf-8") as fh:
            fh.write("\n" + snip.read_text(encoding="utf-8"))
        snip.unlink()

    return step


def set_go_module_prefix(module: str) -> Step:
    """install.sh NEXT: set your module path in .golangci.yml."""

    def step(repo: Repo) -> None:
        cfg = repo.path / ".golangci.yml"
        text = cfg.read_text(encoding="utf-8").replace("github.com/yourorg", module)
        cfg.write_text(text, encoding="utf-8")

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
GITLEAKS_FAILED = r"Detect hardcoded secrets\.+Failed|leaks found"
BASELINE = "packages/eslint-plugin/src/baselines/raw-db-from.json"


def baseline(count: int) -> dict[str, str]:
    return {BASELINE: json.dumps({"src/legacy.ts": count}, indent=2) + "\n"}


# Main records debt of 2, so growth and shrinkage are both measurable.
LEGACY_DEBT = {
    "src/legacy.ts": (
        "declare const db: { query(sql: string): Promise<unknown> };\n"
        'export const a = db.query("select 1");\n'
        'export const b = db.query("select 2");\n'
    ),
    **baseline(2),
}

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
        {
            "src/bad_dal.ts": (
                "declare const db: { query(sql: string): Promise<unknown> };\n"
                'export const rows = db.query("select 1");\n'
            )
        },
        {"lint"},
        r"no-raw-db-client",
    ),
    "secret": C({"src/bad_secret.ts": "export const " + SECRET_LINE}, {"secrets"}, GITLEAKS_FAILED),
    "ratchet": C(baseline(3), {"ratchet"}, r"baseline grew"),
    "ratchet-shrink": C(baseline(1), {"ratchet"}, must_pass=True),
    # Text in a PR body must not be able to switch a gate off.
    "ratchet-bypass": C(
        baseline(3), {"ratchet"}, r"baseline grew", env={"PR_BODY": "[skip-ratchet]"}
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
        {
            "src/data_access/users.ts": (
                "declare const db: { query(sql: string): Promise<unknown> };\n"
                'export const rows = db.query("select 1");\n'
            )
        },
        {"lint"},
        must_pass=True,
    ),
    "env": C(
        {"src/bad_env.ts": 'export const url = process.env["UNDECLARED_URL"];\n'},
        {"env"},
        r"UNDECLARED_URL",
    ),
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
}

PY_CASES = {
    "lint": C({"src/app/bad_lint.py": "import os\n"}, {"ruff"}, r"F401"),
    "types": C({"src/app/bad_types.py": 'count: int = "three"\n'}, {"mypy"}, r"Incompatible types"),
    "format": C({"src/app/bad_format.py": "x=1\n"}, {"format"}, r"bad_format"),
    "test": C(
        {"tests/test_bad.py": "def test_fails() -> None:\n    assert 1 == 2\n"},
        {"pytest"},
        r"test_fails",
    ),
    "dal": C(
        {
            "src/app/bad_dal.py": (
                "from typing import Any\n\n\ndef rows(db: Any) -> Any:\n"
                '    return db.execute("select 1")\n'
            )
        },
        {"pre-commit"},
        r"no-raw-db-query-outside-dal",
    ),
    "secret": C({"src/app/bad_secret.py": SECRET_LINE}, {"secrets"}, GITLEAKS_FAILED),
}

GO_CASES = {
    "lint": C(
        {"bad_lint.go": 'package main\n\nimport "os"\n\nfunc cleanup() {\n\tos.Remove("x")\n}\n'},
        {"golangci-lint"},
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
        {"golangci-lint", "pre-commit"},
        r"raw DB query outside dal|no-raw-db-query-outside-dal",
    ),
    "secret": C(
        {"bad_secret.go": "package main\n\n// " + SECRET_LINE}, {"secrets"}, GITLEAKS_FAILED
    ),
}

PRE_COMMIT_ALL: GateStep = (
    "pre-commit",
    ["pre-commit", "run", "--all-files", "--show-diff-on-failure"],
    "",
)
NPM_INSTALL = cmd("npm", "install", "--no-audit", "--no-fund")
GITLEAKS: GateStep = ("secrets", ["gitleaks", "git", "--no-banner", "--redact", "."], "")
# hardening-polyglot.yml's secrets job. (The pre-commit gitleaks hook scans
# staged changes only, so `pre-commit run --all-files` cannot stand in for it.)
GITLEAKS_POLYGLOT: GateStep = (
    "secrets",
    ["gitleaks", "git", "--no-banner", "--redact", "--config", ".gitleaks.toml", "."],
    "",
)


def node_gate(*extra: GateStep) -> list[GateStep]:
    """The steps hardening-node.yml runs, in order."""
    return [
        ("format", ["npm", "run", "format:check"], ""),
        ("lint", ["npm", "run", "lint"], ""),
        ("typecheck", ["npm", "run", "typecheck"], ""),
        *extra,
        ("env", ["bash", ".github/scripts/check-env-schema.sh"], ""),
        ("test", ["npm", "test"], ""),
        GITLEAKS,
    ]


STACKS: dict[str, Stack] = {
    "ts": Stack(
        fixture="ts",
        setup=[install("ts"), merge_package_snippet(), NPM_INSTALL, write(LEGACY_DEBT)],
        gate=node_gate(("ratchet", ["bash", ".github/scripts/check-baseline-shrinkage.sh"], "")),
        tools=["node", "npm", "bash", "gitleaks"],
        cases=TS_CASES,
    ),
    "js": Stack(
        fixture="js",
        setup=[install("js"), merge_package_snippet(), NPM_INSTALL],
        gate=node_gate(),
        tools=["node", "npm", "bash", "gitleaks"],
        cases=JS_CASES,
    ),
    "python": Stack(
        fixture="python",
        setup=[install("python"), append_pyproject_snippet(), cmd("uv", "lock", "--quiet")],
        gate=[
            # hardening-python.yml installs with --locked: a stale uv.lock fails.
            ("deps", ["uv", "sync", "--locked", "--quiet"], ""),
            ("ruff", ["uv", "run", "ruff", "check", "."], ""),
            ("format", ["uv", "run", "ruff", "format", "--check", "."], ""),
            ("mypy", ["uv", "run", "mypy", "."], ""),
            ("pytest", ["uv", "run", "pytest", "-q"], ""),
            PRE_COMMIT_ALL,
            GITLEAKS_POLYGLOT,
        ],
        tools=["uv", "bash", "git", "gitleaks"],
        cases=PY_CASES,
    ),
    "go": Stack(
        fixture="go",
        setup=[
            install("go"),
            set_go_module_prefix("example.com/fixture"),
            cmd("go", "get", "github.com/quasilyte/go-ruleguard/dsl@v0.3.23"),
            cmd("go", "mod", "tidy"),  # B25: must keep the DSL that rules.go imports
        ],
        gate=[
            ("build", ["go", "build", "./..."], ""),
            ("vet", ["go", "vet", "./..."], ""),
            ("test", ["go", "test", "./..."], ""),
            ("format", ["golangci-lint", "fmt", "--diff"], ""),
            ("golangci-lint", ["golangci-lint", "run", "--new-from-rev=origin/main"], ""),
            PRE_COMMIT_ALL,
            GITLEAKS_POLYGLOT,
        ],
        tools=["go", "golangci-lint", "bash", "git", "gitleaks"],
        cases=GO_CASES,
    ),
    # A TS web package and a Python service in one repo, both variants at the root.
    "mono": Stack(
        fixture="mono",
        setup=[
            install("ts"),
            install("python"),
            merge_package_snippet(),
            append_pyproject_snippet(),
            NPM_INSTALL,
            cmd("uv", "sync", "--quiet"),
        ],
        gate=[
            ("lint", ["npm", "run", "lint"], ""),
            ("typecheck", ["npm", "run", "typecheck"], ""),
            ("ruff", ["uv", "run", "ruff", "check", "."], ""),
            ("mypy", ["uv", "run", "mypy", "."], ""),
            ("ci-has-python", ["bash", "-c", "grep -l ruff .github/workflows/*.yml"], ""),
        ],
        tools=["node", "npm", "uv", "bash"],
        cases={
            "ts-lint": TS_CASES["lint"],
            "py-lint": C({"services/api/bad_lint.py": "import os\n"}, {"ruff"}, r"F401"),
        },
    ),
}


def run_gate(
    stack: Stack, repo: Repo, only: set[str] | None = None, env: dict[str, str] | None = None
) -> dict[str, str]:
    """Run gate steps (all, or only those labelled in `only`).

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
