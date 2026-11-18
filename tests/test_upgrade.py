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


def copier(repo: Repo, *args: str) -> str:
    res = run([*tool("copier"), *args], repo.path, env=NO_INSTALL, timeout=600)
    assert res.ok, res.out
    return res.out


def scripts(repo: Repo) -> dict[str, str]:
    return json.loads((repo.path / "package.json").read_text(encoding="utf-8"))["scripts"]


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
    path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    git(kit, "commit", "-q", "-am", "kit v2")
    git(kit, "tag", "v2.0.0")


def test_update_keeps_user_edits_and_brings_kit_changes(installed: tuple[Path, Repo]) -> None:
    kit, repo = installed
    prettierrc = repo.path / ".prettierrc.json"
    data = json.loads(prettierrc.read_text(encoding="utf-8"))
    data["printWidth"] = 100  # the user's edit to a kit-owned file
    prettierrc.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    (repo.path / "eslint.config.mjs").write_text(
        'import hardening from "./eslint.hardening.mjs";\n\n'
        'export default [...hardening, { rules: { curly: "error" } }];\n',
        encoding="utf-8",
        newline="\n",
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
    (repo.path / "package.json").write_text(
        json.dumps(pkg, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
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


def test_check_script_follows_every_module_change(tmp_path: Path) -> None:
    """Review finding: from a partial module set, `check` went stale or broken."""
    kit = kit_copy(tmp_path / "kit")
    repo = make_repo("js", tmp_path / "user")
    copier(
        repo,
        "copy",
        "--trust",
        "--defaults",
        "--vcs-ref",
        "v1.0.0",
        "--data",
        'stacks=["js"]',
        "--data",
        'modules=["format", "lint"]',
        str(kit),
        str(repo.path),
    )
    assert scripts(repo)["check"] == "npm run format:check && npm run lint"
    repo.commit_all("install")

    def update(modules: str) -> dict[str, str]:
        copier(
            repo,
            "update",
            "--trust",
            "--defaults",
            "--vcs-ref",
            "v1.0.0",
            "--data",
            f"modules={modules}",
        )
        repo.commit_all(f"modules {modules}")
        return scripts(repo)

    s = update('["lint"]')
    assert s["check"] == "npm run lint" and "format:check" not in s
    s = update('["lint", "types", "format"]')
    assert s["check"] == "npm run format:check && npm run lint && npm run typecheck"
    assert s["typecheck"] == "tsc --noEmit -p jsconfig.json"
    s = update('["format", "lint"]')
    assert "typecheck" not in s and not (repo.path / "jsconfig.json").exists()


def test_existing_config_files_are_kept_and_reported(tmp_path: Path) -> None:
    """Review finding: a repo's own eslint/tsconfig got none of the kit's rules, silently."""
    kit = kit_copy(tmp_path / "kit")
    repo = make_repo("ts", tmp_path / "user")
    repo.write("eslint.config.mjs", "export default [];\n")
    repo.write("tsconfig.json", '{ "compilerOptions": { "strict": false } }\n')
    repo.commit_all("existing configs")
    out = copier(
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
    assert (repo.path / "eslint.config.mjs").read_text(encoding="utf-8") == "export default [];\n"
    assert "NOT WIRED" in out
    assert "eslint.config.mjs: add" in out and "tsconfig.json: add" in out
