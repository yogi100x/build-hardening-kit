"""Post-install task for build-hardening-kit, run by copier (needs --trust).

Wires the kit into files the user owns, which a template cannot render:
  * Node: adds the kit's npm scripts and dev dependencies to package.json
    (never overwriting a script you changed), then runs `npm install`.
  * Python: adds the dev tools with `uv add --dev`.
  * Go: makes an existing Makefile include hardening.mk; adds the ruleguard DSL
    when the architecture rules are on.
On `copier update`, scripts of modules you removed are dropped if unchanged.
Set HARDENING_SKIP_INSTALL=1 to skip npm install / uv add / go get.
Uses only the standard library; it runs on copier's own interpreter.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKIP_INSTALL = os.environ.get("HARDENING_SKIP_INSTALL") == "1"

NODE_DEV_DEPS = {
    "format": {"prettier": "^3.10.1"},
    "lint": {"eslint": "^9.39.0", "@eslint/js": "^9.39.0", "globals": "^17.14.0"},
    "lint-ts": {"typescript-eslint": "^8.73.0", "typescript": "^5.9.3"},
    "types": {"typescript": "^5.9.3"},
    "types-js": {"@types/node": "^24.19.0"},
}
PY_DEV_TOOLS = {"base": ["poethepoet", "pytest"], "ruff": ["ruff"], "types": ["mypy"]}
RULEGUARD_DSL = "github.com/quasilyte/go-ruleguard/dsl@v0.3.23"


def say(msg: str) -> None:
    print(f"[hardening] {msg}")


def warn(msg: str) -> None:
    print(f"[hardening] WARNING: {msg}")


def run(argv: list[str]) -> bool:
    exe = shutil.which(argv[0])
    if not exe:
        warn(f"'{argv[0]}' not found; run yourself: {' '.join(argv)}")
        return False
    say("running: " + " ".join(argv))
    res = subprocess.run([exe, *argv[1:]], check=False)
    if res.returncode != 0:
        warn(f"'{' '.join(argv)}' failed (exit {res.returncode}); run it yourself")
    return res.returncode == 0


def node_scripts(ts: bool, modules: set[str]) -> dict[str, str]:
    """Every npm script the kit manages, by module, with the kit's value."""
    scripts: dict[str, str] = {}
    parts = []
    if "format" in modules:
        scripts["format"] = "prettier --write ."
        scripts["format:check"] = "prettier --check ."
        parts.append("npm run format:check")
    if "lint" in modules:
        scripts["lint"] = "eslint . --max-warnings=0"
        parts.append("npm run lint")
    if "types" in modules:
        scripts["typecheck"] = "tsc --noEmit" if ts else "tsc --noEmit -p jsconfig.json"
        parts.append("npm run typecheck")
    if parts:
        scripts["check"] = " && ".join(parts)
    return scripts


ALL_NODE_MODULES = {"format", "lint", "types"}


def apply_node(stacks: list[str], modules: set[str]) -> None:
    pkg_path = Path("package.json")
    if not pkg_path.exists():
        warn("no package.json here; create one (npm init -y) and re-run `copier update --trust`")
        return
    raw = pkg_path.read_text(encoding="utf-8")
    indent_match = re.search(r'^\{\s*\n([ \t]+)"', raw)
    indent = indent_match.group(1) if indent_match else "  "
    pkg = json.loads(raw)
    ts = "ts" in stacks

    wanted = node_scripts(ts, modules)
    every = {**node_scripts(ts, ALL_NODE_MODULES), **node_scripts(not ts, ALL_NODE_MODULES)}
    scripts = pkg.setdefault("scripts", {})
    for name, value in wanted.items():
        current = scripts.get(name)
        if current is None:
            scripts[name] = value
        elif current != value and current not in every.values():
            warn(f"kept your npm script '{name}' ({current!r}); the kit's is {value!r}")
        else:
            scripts[name] = value
    for name, value in every.items():
        # A module was removed: drop its script only if it is still the kit's.
        if name not in wanted and scripts.get(name) == value:
            del scripts[name]
    if "test" not in scripts:
        warn("package.json has no 'test' script; CI runs `npm test`, so add one")

    deps = pkg.setdefault("devDependencies", {})
    keys = [m for m in ("format", "lint", "types") if m in modules]
    if "lint" in modules and ts:
        keys.append("lint-ts")
    if "types" in modules and not ts:
        keys.append("types-js")
    for key in keys:
        for dep, version in NODE_DEV_DEPS[key].items():
            deps.setdefault(dep, version)
    pkg["devDependencies"] = dict(sorted(deps.items()))

    new = json.dumps(pkg, indent=indent, ensure_ascii=False) + "\n"
    if new != raw:
        pkg_path.write_text(new, encoding="utf-8")
        say("updated package.json (scripts, devDependencies)")
    if not SKIP_INSTALL:
        run(["npm", "install", "--no-audit", "--no-fund"])


def apply_python(modules: set[str]) -> None:
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        warn("no pyproject.toml here; create one (uv init) and re-run `copier update --trust`")
        return
    text = pyproject.read_text(encoding="utf-8")
    if Path("ruff.toml").exists() and re.search(r"^\[tool\.ruff", text, re.MULTILINE):
        warn(
            "ruff.toml now takes precedence over pyproject.toml [tool.ruff]; move those settings into ruff.toml"
        )
    if Path("mypy.ini").exists() and re.search(r"^\[tool\.mypy", text, re.MULTILINE):
        warn("mypy.ini now takes precedence over pyproject.toml [tool.mypy]; keep one of them")
    tools = list(PY_DEV_TOOLS["base"])
    if {"lint", "format"} & modules:
        tools += PY_DEV_TOOLS["ruff"]
    if "types" in modules:
        tools += PY_DEV_TOOLS["types"]
    missing = [t for t in tools if not re.search(rf'["\']{re.escape(t)}([<>=~!\[; "\']|$)', text)]
    if missing and not SKIP_INSTALL:
        run(["uv", "add", "--dev", *missing])
    elif missing:
        say("add the dev tools: uv add --dev " + " ".join(missing))
    say("commit uv.lock: CI installs with `uv sync --locked`")


def apply_go(modules: set[str]) -> None:
    makefile = Path("Makefile")
    if makefile.exists():
        text = makefile.read_text(encoding="utf-8")
        if not re.search(r"^-?include\s+hardening\.mk\s*$", text, re.MULTILINE):
            makefile.write_text(text.rstrip("\n") + "\n\ninclude hardening.mk\n", encoding="utf-8")
            say("added `include hardening.mk` to your Makefile")
    gomod = Path("go.mod")
    if (
        "arch-rules" in modules
        and gomod.exists()
        and "go-ruleguard/dsl" not in gomod.read_text(encoding="utf-8")
    ):
        if SKIP_INSTALL:
            say(f"add the ruleguard DSL: go get {RULEGUARD_DSL}")
        else:
            run(["go", "get", RULEGUARD_DSL])


def next_steps(stacks: list[str], modules: set[str]) -> None:
    lines = []
    if "ts" in stacks or "js" in stacks:
        lines.append("Node:   npm run check && npm test")
        if "lint" in modules:
            lines.append(
                "        existing lint problems? record them once: npx eslint --suppress-all ."
            )
    if "python" in stacks:
        lines.append("Python: uv run poe check && uv run poe test")
    if "go" in stacks:
        lines.append("Go:     make check && make test")
    if "hooks" in modules:
        lines.append("Hooks:  uvx pre-commit install")
    if "governance" in modules:
        lines.append("Merge protection: see docs/BRANCH_PROTECTION.md in the kit")
    say("done. Run the gate locally:")
    for line in lines:
        print("    " + line)


def main() -> int:
    answers = json.loads(sys.argv[1])
    stacks: list[str] = answers["stacks"]
    modules = set(answers["modules"])
    if "ts" in stacks or "js" in stacks:
        apply_node(stacks, modules)
    if "python" in stacks:
        apply_python(modules)
    if "go" in stacks:
        apply_go(modules)
    next_steps(stacks, modules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
