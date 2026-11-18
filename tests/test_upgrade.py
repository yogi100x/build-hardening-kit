"""Upgrade, module removal and user-owned files, through `copier update`.

A throwaway copy of the kit is tagged v1, installed, then changed and tagged
v2, the way a release would be; the user's repo is edited in between.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from harness import KIT, Repo, git, make_repo, run, tool

IGNORE = shutil.ignore_patterns(".git", ".venv", "__pycache__", ".pytest_cache", "node_modules")
NO_INSTALL = {"HARDENING_SKIP_INSTALL": "1"}


def kit_copy(dest: Path) -> Path:
    shutil.copytree(KIT, dest, ignore=IGNORE)
    git(dest, "init", "-q", "-b", "main")
    git(dest, "config", "user.email", "selftest@example.invalid")
    git(dest, "config", "user.name", "selftest")
    git(dest, "add", "-A")
    git(dest, "commit", "-q", "-m", "kit v1")
    git(dest, "tag", "v1.0.0")
    return dest


def copier(repo: Repo, *args: str) -> None:
    res = run([*tool("copier"), *args], repo.path, env=NO_INSTALL, timeout=600)
    assert res.ok, res.out


@pytest.fixture()
def installed(tmp_path: Path) -> tuple[Path, Repo]:
    kit = kit_copy(tmp_path / "kit")
    repo = make_repo("ts", tmp_path / "user")
    copier(
        repo,
        "copy",
        "--trust",
        "--defaults",
        "--vcs-ref",
        "v1.0.0",
        "--data",
        'stacks=["ts"]',
        str(kit),
        str(repo.path),
    )
    repo.commit_all("install kit v1")
    return kit, repo


def release_v2(kit: Path, rel: str, old: str, new: str) -> None:
    path = kit / rel
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new), encoding="utf-8")
    git(kit, "commit", "-q", "-am", "kit v2")
    git(kit, "tag", "v2.0.0")


def test_update_keeps_user_edits_and_brings_kit_changes(installed: tuple[Path, Repo]) -> None:
    kit, repo = installed
    prettierrc = repo.path / ".prettierrc.json"
    data = json.loads(prettierrc.read_text(encoding="utf-8"))
    data["printWidth"] = 100  # the user's edit to a kit-owned file
    prettierrc.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (repo.path / "eslint.config.mjs").write_text(
        'import hardening from "./eslint.hardening.mjs";\n\n'
        'export default [...hardening, { rules: { curly: "error" } }];\n',
        encoding="utf-8",
    )
    repo.commit_all("user edits")
    release_v2(
        kit,
        "template/[% if node_format %].prettierrc.json[% endif %]",
        '"endOfLine": "lf"',
        '"endOfLine": "lf",\n  "bracketSameLine": true',
    )

    copier(repo, "update", "--trust", "--defaults", "--vcs-ref", "v2.0.0")

    merged = prettierrc.read_text(encoding="utf-8")
    assert "<<<<<<<" not in merged, merged
    assert json.loads(merged) == {**data, "bracketSameLine": True}
    # A user-owned entry file is never overwritten.
    assert "curly" in (repo.path / "eslint.config.mjs").read_text(encoding="utf-8")


def test_removing_a_module_removes_its_files_and_scripts(installed: tuple[Path, Repo]) -> None:
    _, repo = installed
    pkg = json.loads((repo.path / "package.json").read_text(encoding="utf-8"))
    assert pkg["scripts"]["format:check"] == "prettier --check ."
    pkg["scripts"]["format"] = "prettier --write src"  # the user changed this one
    (repo.path / "package.json").write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
    repo.commit_all("user script")

    copier(
        repo,
        "update",
        "--trust",
        "--defaults",
        "--vcs-ref",
        "v1.0.0",
        "--data",
        'modules=["lint", "types", "secrets", "ci"]',
    )

    assert not (repo.path / ".prettierrc.json").exists()
    assert not (repo.path / ".pre-commit-config.yaml").exists()
    after = json.loads((repo.path / "package.json").read_text(encoding="utf-8"))["scripts"]
    assert "format:check" not in after
    assert after["format"] == "prettier --write src"  # user-changed scripts stay
    assert after["check"] == "npm run lint && npm run typecheck"
