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
KIT_MAKE_TARGETS = ("fmt", "fmt-check", "lint", "vet", "test", "build", "check")


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


NODE_MODULES = ("format", "lint", "types")


def known_kit_scripts() -> dict[str, set[str]]:
    """Every value the kit has ever written for each script: both stacks and
    every combination of modules. A script holding one of these is the kit's;
    anything else was changed by the user and is never touched."""
    known: dict[str, set[str]] = {}
    for ts in (True, False):
        for mask in range(1 << len(NODE_MODULES)):
            subset = {m for i, m in enumerate(NODE_MODULES) if mask & (1 << i)}
            for name, value in node_scripts(ts, subset).items():
                known.setdefault(name, set()).add(value)
    return known


LOCKFILES = {"package-lock.json": "npm", "pnpm-lock.yaml": "pnpm", "yarn.lock": "yarn"}
INSTALL = {
    "npm": ["npm", "install", "--no-audit", "--no-fund"],
    "pnpm": ["pnpm", "install"],
    "yarn": ["yarn", "install"],
}


def write_lf(path: Path, text: str) -> None:
    """Write with LF line endings on every OS (the kit's Prettier enforces LF)."""
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def warn_unwired(path: str, needle: str, how: str) -> None:
    """An entry file the user already had is kept as is; say so loudly if it
    does not pull in the kit's file, because then the kit's rules do nothing."""
    p = Path(path)
    if p.exists() and needle not in p.read_text(encoding="utf-8"):
        UNWIRED.append(f"{path}: {how}")


UNWIRED: list[str] = []


def apply_node(stacks: list[str], modules: set[str], package_manager: str) -> None:
    pkg_path = Path("package.json")
    if not pkg_path.exists():
        warn("no package.json here; create one (npm init -y) and re-run `copier update --trust`")
        return
    raw = pkg_path.read_text(encoding="utf-8")
    indent_match = re.search(r'^\{\s*\n([ \t]+)"', raw)
    indent = indent_match.group(1) if indent_match else "  "
    pkg = json.loads(raw)
    ts = "ts" in stacks

    wanted = node_scripts(ts, modules & set(NODE_MODULES))
    known = known_kit_scripts()
    scripts = pkg.setdefault("scripts", {})
    for name, value in wanted.items():
        current = scripts.get(name)
        if current is None or current in known[name]:
            scripts[name] = value
        elif current != value:
            warn(f"kept your npm script '{name}' ({current!r}); the kit's is {value!r}")
    for name, values in known.items():
        # A module was removed: drop its script only if it is still the kit's.
        if name not in wanted and scripts.get(name) in values:
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
        write_lf(pkg_path, new)
        say("updated package.json (scripts, devDependencies)")

    if "lint" in modules:
        warn_unwired(
            "eslint.config.mjs",
            "eslint.hardening.mjs",
            'add `import hardening from "./eslint.hardening.mjs";` and spread `...hardening` '
            "first in the exported array",
        )
    if ts and {"types", "lint"} & modules:
        warn_unwired(
            "tsconfig.json",
            "tsconfig.hardening.json",
            'add `"extends": "./tsconfig.hardening.json"`',
        )
    if not ts and "types" in modules:
        warn_unwired(
            "jsconfig.json",
            "jsconfig.hardening.json",
            'add `"extends": "./jsconfig.hardening.json"`',
        )

    lock = next((pm for f, pm in LOCKFILES.items() if Path(f).exists()), None)
    if lock and lock != package_manager:
        warn(
            f"found a {lock} lockfile but the kit was set up for {package_manager}; "
            f"re-run with --data node_package_manager={lock}"
        )
    if not SKIP_INSTALL:
        run(INSTALL[package_manager])


def apply_python(modules: set[str]) -> None:
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        warn("no pyproject.toml here; create one (uv init) and re-run `copier update --trust`")
        return
    text = pyproject.read_text(encoding="utf-8")
    if {"lint", "format"} & modules:
        warn_unwired("ruff.toml", "ruff.hardening.toml", 'add `extend = "ruff.hardening.toml"`')
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
    present = dev_dependencies(text)
    missing = [t for t in tools if t not in present]
    if missing and not SKIP_INSTALL:
        run(["uv", "add", "--dev", *missing])
    elif missing:
        say("add the dev tools: uv add --dev " + " ".join(missing))
    if not Path("uv.lock").exists() and not SKIP_INSTALL:
        run(["uv", "lock"])
    say("commit uv.lock: CI installs with `uv sync --locked`")


def dev_dependencies(pyproject_text: str) -> set[str]:
    """Names in the dev group uv installs by default (`uv sync`): the `dev`
    dependency group and [tool.uv] dev-dependencies. Optional extras do not
    count: CI's `uv sync --locked` does not install them."""
    try:
        import tomllib
    except ModuleNotFoundError:  # Python < 3.11: assume nothing is present
        return set()
    data = tomllib.loads(pyproject_text)
    specs = list((data.get("dependency-groups") or {}).get("dev") or [])
    specs += list(((data.get("tool") or {}).get("uv") or {}).get("dev-dependencies") or [])
    names = set()
    for spec in specs:
        if isinstance(spec, str):
            m = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", spec)
            if m:
                names.add(m.group(1).lower().replace("_", "-"))
    return names


def apply_go(modules: set[str]) -> None:
    makefile = Path("Makefile")
    if makefile.exists():
        text = makefile.read_text(encoding="utf-8")
        if not re.search(r"^-?include\s+hardening\.mk\s*$", text, re.MULTILINE):
            write_lf(makefile, text.rstrip("\n") + "\n\ninclude hardening.mk\n")
            say("added `include hardening.mk` to your Makefile")
        clashes = sorted(
            t
            for t in KIT_MAKE_TARGETS
            if re.search(rf"^{re.escape(t)}\s*:(?!=)", text, re.MULTILINE)
        )
        if clashes:
            warn(
                "your Makefile already defines " + ", ".join(clashes) + "; hardening.mk "
                "defines them too, and make runs whichever comes last (it prints "
                "'overriding commands'). Rename yours or drop them."
            )
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
    if UNWIRED:
        print()
        warn("NOT WIRED — these files existed before, so the kit kept them as they")
        warn("are, and they do not use the kit's rules yet. Until you add one line")
        warn("to each, those checks run without the kit's settings:")
        for item in UNWIRED:
            print("    - " + item)


def main() -> int:
    answers = json.loads(sys.argv[1])
    stacks: list[str] = answers["stacks"]
    modules = set(answers["modules"])
    if "ts" in stacks or "js" in stacks:
        apply_node(stacks, modules, answers.get("node_package_manager") or "npm")
    if "python" in stacks:
        apply_python(modules)
    if "go" in stacks:
        apply_go(modules)
    next_steps(stacks, modules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
