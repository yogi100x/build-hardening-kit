"""What each stack installs, how it is set up, and which commands are its gate.

This table follows the kit's own documentation (README, install.sh NEXT lines,
CI snippets) so the self-test checks what a user following the docs gets.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field

from harness import KIT, Repo, bash, run, tool

Step = Callable[[Repo], None]


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
        cfg.write_text(
            cfg.read_text(encoding="utf-8").replace("github.com/yourorg", module), encoding="utf-8"
        )

    return step


def cmd(*argv: str, cwd: str = "") -> Step:
    def step(repo: Repo) -> None:
        exe = tool(argv[0])
        res = run([*exe, *argv[1:]], repo.path / cwd if cwd else repo.path)
        if not res.ok:
            raise RuntimeError(f"{' '.join(argv)} failed:\n{res.out}")

    return step


@dataclass
class Violation:
    files: dict[str, str]
    # Gate step labels expected to catch it. The case passes only when one of
    # these steps passes on the clean repo and fails with the violation planted.
    caught_by: set[str]
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class Stack:
    fixture: str
    setup: list[Step]
    # Each gate: (label, argv, cwd relative to repo root).
    gate: list[tuple[str, list[str], str]]
    tools: list[str]
    violations: dict[str, Violation] = field(default_factory=dict)


SECRET_LINE = 'AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYzXq9Lr4Tq2"\n'

V = Violation
GROWN_BASELINE = {
    "packages/eslint-plugin/src/baselines/raw-db-from.json": '{\n  "src/x.ts": 3\n}\n'
}

TS_VIOLATIONS = {
    "lint": V(
        {
            "src/bad_lint.ts": "export function same(a: number, b: number): boolean {\n  return a == b;\n}\n"
        },
        {"lint"},
    ),
    "types": V({"src/bad_types.ts": 'export const count: number = "three";\n'}, {"typecheck"}),
    "format": V({"src/bad_format.ts": "export const   spaced =1\n"}, {"lint", "format"}),
    "dal": V(
        {
            "src/bad_dal.ts": (
                "declare const db: { query(sql: string): Promise<unknown> };\n"
                'export const rows = db.query("select 1");\n'
            )
        },
        {"lint"},
    ),
    "secret": V({"src/bad_secret.ts": "export const " + SECRET_LINE}, {"secrets"}),
    "ratchet": V(GROWN_BASELINE, {"ratchet"}),
    # Text in a PR body must not be able to switch a gate off.
    "ratchet-bypass": V(GROWN_BASELINE, {"ratchet"}, env={"PR_BODY": "[skip-ratchet]"}),
}

JS_VIOLATIONS = {
    "lint": V({"src/bad_lint.js": "export function same(a, b) {\n  return a == b;\n}\n"}, {"lint"}),
    "types": V(
        {"src/bad_types.js": '/** @type {number} */\nexport const count = "three";\n'},
        {"typecheck"},
    ),
    "format": V({"src/bad_format.js": "export const   spaced =1\n"}, {"lint", "format"}),
    "dal": V(
        {
            "src/bad_dal.js": 'const db = { query: async (/** @type {string} */ s) => s };\nexport const rows = db.query("select 1");\n'
        },
        {"lint"},
    ),
}

PY_VIOLATIONS = {
    "lint": V({"src/app/bad_lint.py": "import os\n"}, {"ruff"}),
    "types": V({"src/app/bad_types.py": 'count: int = "three"\n'}, {"mypy"}),
    "format": V({"src/app/bad_format.py": "x=1\n"}, {"format"}),
    "test": V({"tests/test_bad.py": "def test_fails() -> None:\n    assert 1 == 2\n"}, {"pytest"}),
    "dal": V(
        {
            "src/app/bad_dal.py": 'from typing import Any\n\n\ndef rows(db: Any) -> Any:\n    return db.execute("select 1")\n'
        },
        {"pre-commit"},
    ),
    "secret": V({"src/app/bad_secret.py": SECRET_LINE}, {"pre-commit"}),
}

GO_VIOLATIONS = {
    "lint": V(
        {"bad_lint.go": 'package main\n\nimport "os"\n\nfunc cleanup() {\n\tos.Remove("x")\n}\n'},
        {"golangci-lint"},
    ),
    "types": V({"bad_types.go": 'package main\n\nvar count int = "three"\n'}, {"build"}),
    "format": V({"bad_format.go": "package main\n\nvar   spaced=1\n"}, {"golangci-lint", "format"}),
    "test": V(
        {
            "bad_test.go": 'package main\n\nimport "testing"\n\nfunc TestFails(t *testing.T) { t.Fatal("planted") }\n'
        },
        {"test"},
    ),
    "dal": V(
        {
            "bad_dal.go": (
                'package main\n\nimport "database/sql"\n\n'
                'func rows(db *sql.DB) error {\n\t_, err := db.Query("select 1")\n\treturn err\n}\n'
            )
        },
        {"golangci-lint", "pre-commit"},
    ),
    "secret": V({"bad_secret.go": "package main\n\n// " + SECRET_LINE}, {"pre-commit"}),
}

PRE_COMMIT_ALL = ("pre-commit", ["pre-commit", "run", "--all-files", "--show-diff-on-failure"], "")

STACKS: dict[str, Stack] = {
    "ts": Stack(
        fixture="ts",
        setup=[
            install("ts"),
            merge_package_snippet(),
            cmd("npm", "install", "--no-audit", "--no-fund"),
        ],
        gate=[
            ("lint", ["npm", "run", "lint"], ""),
            ("typecheck", ["npm", "run", "typecheck"], ""),
            ("ratchet", ["bash", ".github/scripts/check-baseline-shrinkage.sh"], ""),
        ],
        tools=["node", "npm", "bash"],
        violations=TS_VIOLATIONS,
    ),
    "js": Stack(
        fixture="js",
        setup=[
            install("js"),
            merge_package_snippet(),
            cmd("npm", "install", "--no-audit", "--no-fund"),
        ],
        gate=[("lint", ["npm", "run", "lint"], ""), ("typecheck", ["npm", "run", "typecheck"], "")],
        tools=["node", "npm", "bash"],
        violations=JS_VIOLATIONS,
    ),
    "python": Stack(
        fixture="python",
        setup=[install("python"), append_pyproject_snippet(), cmd("uv", "sync", "--quiet")],
        gate=[
            ("ruff", ["uv", "run", "ruff", "check", "."], ""),
            ("format", ["uv", "run", "ruff", "format", "--check", "."], ""),
            ("mypy", ["uv", "run", "mypy", "."], ""),
            ("pytest", ["uv", "run", "pytest", "-q"], ""),
            PRE_COMMIT_ALL,
        ],
        tools=["uv", "bash", "git"],
        violations=PY_VIOLATIONS,
    ),
    "go": Stack(
        fixture="go",
        setup=[install("go"), set_go_module_prefix("example.com/fixture")],
        gate=[
            ("build", ["go", "build", "./..."], ""),
            ("vet", ["go", "vet", "./..."], ""),
            ("test", ["go", "test", "./..."], ""),
            ("golangci-lint", ["golangci-lint", "run"], ""),
            PRE_COMMIT_ALL,
        ],
        tools=["go", "golangci-lint", "bash", "git"],
        violations=GO_VIOLATIONS,
    ),
    # A TS web package and a Python service in one repo, both variants at the root.
    "mono": Stack(
        fixture="mono",
        setup=[
            install("ts"),
            install("python"),
            merge_package_snippet(),
            append_pyproject_snippet(),
            cmd("npm", "install", "--no-audit", "--no-fund"),
            cmd("uv", "sync", "--quiet"),
        ],
        gate=[
            ("lint", ["npm", "run", "lint"], ""),
            ("typecheck", ["npm", "run", "typecheck"], ""),
            ("ruff", ["uv", "run", "ruff", "check", "."], ""),
            ("mypy", ["uv", "run", "mypy", "."], ""),
            ("ci-has-python", ["bash", "-c", "grep -q 'ruff' .github/workflows/*.yml"], ""),
        ],
        tools=["node", "npm", "uv", "bash"],
        violations={
            "ts-lint": TS_VIOLATIONS["lint"],
            "py-lint": V({"services/api/bad_lint.py": "import os\n"}, {"ruff"}),
        },
    ),
}


def gate_failures(stack: Stack, repo: Repo, env: dict[str, str] | None = None) -> dict[str, str]:
    """Run every gate step; return {label: output tail} for each that failed."""
    failures = {}
    for label, argv, cwd in stack.gate:
        exe = tool(argv[0])
        res = run([*exe, *argv[1:]], repo.path / cwd if cwd else repo.path, env=env)
        if not res.ok:
            failures[label] = res.out[-4000:]
    return failures
