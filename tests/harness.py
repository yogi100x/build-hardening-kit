"""Helpers for installing the kit into throwaway fixture repos and running gates.

Each test copies a fixture under tests/fixtures/ into a temp dir, makes it a git
repo with an `origin/main` (ratchets and `--new-from-rev` need one), installs
the kit the way the README documents, then runs the stack's check commands.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1]
FIXTURES = KIT / "tests" / "fixtures"
IS_WINDOWS = sys.platform == "win32"

# In CI a missing tool is a failure, never a silent skip.
REQUIRE_TOOLS = os.environ.get("BHK_REQUIRE_TOOLS") == "1"


# Python-distributed tools fetched with uvx when not installed, pinned so a PR
# run does not pick up whatever was released that day (nightly runs catch drift).
UVX_PINS = {
    "pre-commit": "pre-commit@4.7.0",
    "semgrep": "semgrep@1.186.0",
    "zizmor": "zizmor@1.32.0",
}


@dataclass
class Result:
    code: int
    out: str

    @property
    def ok(self) -> bool:
        return self.code == 0


def tool(name: str) -> list[str]:
    """Resolve a CLI, falling back to `uvx` for Python-distributed tools."""
    found = shutil.which(name)
    if found:
        return [found]
    if name in UVX_PINS and shutil.which("uvx"):
        return [shutil.which("uvx") or "uvx", UVX_PINS[name]]
    msg = f"required tool not found: {name}"
    if REQUIRE_TOOLS:
        pytest.fail(msg)
    pytest.skip(msg)
    raise AssertionError("unreachable")


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 900) -> Result:
    # PR_* would leak a developer's own PR text into the ratchet; drop it.
    base = {k: v for k, v in os.environ.items() if not k.startswith("PR_")}
    full_env = {**base, "TZ": "UTC", "CI": "1", **(env or {})}
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=full_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    return Result(proc.returncode, proc.stdout)


def git(repo: Path, *args: str) -> Result:
    res = run(["git", *args], repo)
    if not res.ok:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{res.out}")
    return res


class Repo:
    def __init__(self, path: Path) -> None:
        self.path = path

    def write(self, rel: str, content: str) -> None:
        target = self.path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")

    def commit_all(self, message: str) -> None:
        git(self.path, "add", "-A")
        git(self.path, "commit", "-q", "--no-verify", "--allow-empty", "-m", message)

    def plant(self, files: dict[str, str]) -> None:
        """Put a violation on a `pr` branch, as a pull request would."""
        self.reset()  # hooks may have rewritten files during an earlier run
        git(self.path, "checkout", "-q", "-B", "pr", "main")
        for rel, content in files.items():
            self.write(rel, content)
        self.commit_all("plant violation")

    def reset(self) -> None:
        git(self.path, "checkout", "-q", "-f", "main")
        # -x also drops ignored caches (.mypy_cache, .ruff_cache); keep installs.
        git(self.path, "clean", "-q", "-fdx", "-e", "node_modules", "-e", ".venv")


def make_repo(fixture: str, dest: Path) -> Repo:
    """Copy a fixture into dest/work, with dest/remote.git as its origin."""
    work = dest / "work"
    shutil.copytree(FIXTURES / fixture, work)
    remote = dest / "remote.git"
    run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], dest)
    git(work, "init", "-q", "-b", "main")
    git(work, "config", "user.email", "selftest@example.invalid")
    git(work, "config", "user.name", "selftest")
    git(work, "config", "core.autocrlf", "false")
    git(work, "remote", "add", "origin", str(remote))
    repo = Repo(work)
    repo.commit_all("fixture")
    return repo


def publish_main(repo: Repo) -> None:
    """Push main so origin/main exists for ratchets and new-from-rev."""
    git(repo.path, "push", "-q", "origin", "main")
    git(repo.path, "fetch", "-q", "origin")


def bash() -> list[str]:
    return tool("bash")
