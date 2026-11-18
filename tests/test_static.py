"""Static checks on the kit's own files: things a fixture run cannot see.

Each check names the bug it guards (tests/KNOWN_BUGS.md).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from harness import KIT, run, tool

WORKFLOWS = sorted(
    [
        *KIT.glob(".github/workflows/*.yml"),
        *KIT.glob("shared/.github/workflows/*.yml"),
        *KIT.glob("*/hardening-*.yml"),
    ]
)
SHA = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def steps(wf: dict) -> list[dict]:
    return [s for job in wf.get("jobs", {}).values() for s in job.get("steps", [])]


def test_workflows_found() -> None:
    names = {p.name for p in WORKFLOWS}
    assert {"hardening-node.yml", "hardening-go.yml", "hardening-python.yml"} <= names
    assert {"hardening-polyglot.yml", "codeql.yml", "self-test.yml"} <= names


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_actions_pinned_by_sha(path: Path) -> None:
    """B02: a tag can be moved to other code; a commit SHA cannot."""
    for step in steps(load(path)):
        uses = step.get("uses")
        if uses and not uses.startswith("./"):
            assert SHA.match(uses), f"{path.name}: '{uses}' is not pinned to a commit SHA"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_least_privilege_permissions(path: Path) -> None:
    """B02: top-level permissions empty; each job asks for what it needs."""
    wf = load(path)
    assert wf.get("permissions") == {}, f"{path.name}: top-level permissions must be {{}}"
    for name, job in wf.get("jobs", {}).items():
        assert "permissions" in job, f"{path.name}: job '{name}' declares no permissions"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_main_runs_never_cancelled(path: Path) -> None:
    """B30: a cancelled main run records nothing for later PRs to compare against."""
    group = load(path).get("concurrency") or {}
    cancel = group.get("cancel-in-progress", False) if isinstance(group, dict) else False
    assert cancel is not True, f"{path.name}: cancel-in-progress must exclude main"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_checkout_drops_credentials(path: Path) -> None:
    for step in steps(load(path)):
        if str(step.get("uses", "")).startswith("actions/checkout@"):
            assert (step.get("with") or {}).get("persist-credentials") is False, path.name


def test_codeql_input_name() -> None:
    """B12: the init action reads `languages`; `language` is silently ignored."""
    for step in steps(load(KIT / ".github/workflows/codeql.yml")):
        if "codeql-action/init" in str(step.get("uses", "")):
            assert "languages" in step["with"] and "language" not in step["with"]


def test_no_unpinned_installs() -> None:
    """B03/B29: every tool fetched in CI or hooks has an exact version."""
    for path in WORKFLOWS:
        for step in steps(load(path)):
            script = str(step.get("run", ""))
            assert not re.search(r"pip install (?![^\n]*==)", script), f"{path.name}: {script}"
            for m in re.finditer(r"uvx (\S+)", script):
                assert "@" in m.group(1), f"{path.name}: uvx {m.group(1)} has no version"
    hooks = load(KIT / "polyglot/.pre-commit-config.yaml")
    for repo in hooks["repos"]:
        for hook in repo["hooks"]:
            for dep in hook.get("additional_dependencies", []):
                assert "==" in dep, f"pre-commit hook {hook['id']}: '{dep}' not pinned"


def test_no_archived_hook_repos() -> None:
    """B27: pre-commit/mirrors-prettier is archived."""
    hooks = load(KIT / "polyglot/.pre-commit-config.yaml")
    urls = {r["repo"] for r in hooks["repos"]}
    assert "https://github.com/pre-commit/mirrors-prettier" not in urls


def test_golangci_config_is_v2() -> None:
    """B04/B26: v2 schema; new-from-rev set in one place only."""
    cfg = load(KIT / "go/.golangci.yml")
    assert cfg.get("version") == "2"
    assert "new-from-rev" not in (KIT / "go/Makefile.snippet").read_text(encoding="utf-8")
    assert "fmt --diff" in (KIT / "go/Makefile.snippet").read_text(encoding="utf-8")


def test_codeowners_has_no_live_placeholder() -> None:
    """B21: a nonexistent owner makes GitHub skip the code-owner requirement."""
    for line in (KIT / ".github/CODEOWNERS").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            assert "your-org" not in line, f"live placeholder owner: {line}"


def test_dal_directories_agree() -> None:
    """B13: policy, ESLint rule, baseline generator and semgrep exempt the same dirs."""
    names = {"dal", "data-access", "data_access"}
    rule = (KIT / "shared/eslint-plugin-template/src/rules/no-raw-db-client.js").read_text(
        encoding="utf-8"
    )
    gen = (KIT / "shared/eslint-plugin-template/scripts/generate-baseline.mjs").read_text(
        encoding="utf-8"
    )
    semgrep = (KIT / "polyglot/semgrep/rules.yml").read_text(encoding="utf-8")
    policy = (KIT / "DAL_POLICY.md").read_text(encoding="utf-8")
    for name in names:
        assert name in rule and name in gen, name
        assert f"**/{name}/**" in semgrep, name
        assert f"`{name}/`" in policy, name


def test_docs_cite_only_real_rules() -> None:
    """B20: GOOGLE_GRADE.md must not promise rules the kit does not ship."""
    text = (KIT / "GOOGLE_GRADE.md").read_text(encoding="utf-8")
    assert "any-requires-justification" not in text
    assert "// WHY:" not in text
    assert "coverage gate |" not in text


def test_installable_files_pass_prettier() -> None:
    """B33: the kit's own formatter must accept every file it installs."""
    npx = tool("npx")
    files = [
        "ts/eslint.config.mjs",
        "ts/tsconfig.json",
        "ts/package.snippet.json",
        "js/eslint.config.mjs",
        "js/jsconfig.json",
        "js/package.snippet.json",
        "go/hardening-go.yml",
        "go/.golangci.yml",
        "python/hardening-python.yml",
        "polyglot/hardening-polyglot.yml",
        "polyglot/.pre-commit-config.yaml",
        "polyglot/semgrep/rules.yml",
        "shared/.github/workflows/hardening-node.yml",
        ".github/workflows/codeql.yml",
        ".github/dependabot.yml",
    ]
    res = run(
        [
            *npx,
            "--yes",
            "prettier@3.10.1",
            "--config",
            "shared/.prettierrc.json",
            "--check",
            *files,
        ],
        KIT,
    )
    assert res.ok, res.out
