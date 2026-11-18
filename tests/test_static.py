"""Static checks on what the kit renders, for things a fixture run cannot see.

The template is rendered (tasks skipped) for every stack and both presets, and
the checks run on the rendered files and on the kit's own workflows. Each check
names the bug it guards (tests/KNOWN_BUGS.md).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml
from harness import KIT, run, tool

SHA = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")
ALL = ["format", "lint", "types", "secrets", "ci", "hooks", "governance", "arch-rules"]
RENDERS = {
    "ts-py-go-all": (["ts", "python", "go"], ALL, {"go_module": "example.com/x"}),
    "js-all": (["js"], ALL, {}),
    "py-owners": (["python"], ALL, {"code_owners": "@acme/core"}),
    "ts-minimal": (["ts"], None, {"preset": "minimal"}),
}


def render(dest: Path, stacks: list[str], modules: list[str] | None, data: dict[str, str]) -> Path:
    args = ["--data", f"stacks={json.dumps(stacks)}"]
    if modules is not None:
        args += ["--data", f"modules={json.dumps(modules)}"]
    for key, value in data.items():
        args += ["--data", f"{key}={value}"]
    res = run(
        [
            *tool("copier"),
            "copy",
            "--trust",
            "--defaults",
            "--skip-tasks",
            "--vcs-ref",
            "HEAD",
            *args,
            str(KIT),
            str(dest),
        ],
        KIT,
    )
    assert res.ok, res.out
    return dest


@pytest.fixture(scope="module")
def rendered(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return {name: render(tmp_path_factory.mktemp(name), *spec) for name, spec in RENDERS.items()}


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def steps(wf: dict) -> list[dict]:
    return [s for job in wf.get("jobs", {}).values() for s in job.get("steps", [])]


def workflows(rendered: dict[str, Path]) -> list[Path]:
    out = sorted(KIT.glob(".github/workflows/*.yml"))
    for root in rendered.values():
        out += sorted(root.glob(".github/workflows/*.yml"))
    return out


def test_render_contents(rendered: dict[str, Path]) -> None:
    """Modules decide files; minimal leaves out hooks and governance."""
    full = rendered["ts-py-go-all"]
    for rel in [
        ".github/workflows/hardening.yml",
        ".github/workflows/codeql.yml",
        ".github/CODEOWNERS",
        ".github/dependabot.yml",
        ".pre-commit-config.yaml",
        ".gitleaks.toml",
        "eslint.config.mjs",
        "eslint.hardening.mjs",
        "tsconfig.json",
        "tsconfig.hardening.json",
        "tools/hardening/index.mjs",
        "ruff.toml",
        "ruff.hardening.toml",
        "mypy.ini",
        "poe_tasks.toml",
        ".golangci.yml",
        "hardening.mk",
        "Makefile",
        "hardening_rules.go",
        ".semgrep/hardening.yml",
        ".copier-answers.yml",
    ]:
        assert (full / rel).is_file(), rel
    minimal = rendered["ts-minimal"]
    for rel in [".pre-commit-config.yaml", ".github/CODEOWNERS", "tools", ".semgrep"]:
        assert not (minimal / rel).exists(), rel
    assert (minimal / ".github/workflows/hardening.yml").is_file()


def test_rendered_files_parse(rendered: dict[str, Path]) -> None:
    """Every rendered YAML/JSON file is valid (template logic cannot break syntax)."""
    for root in rendered.values():
        for path in [*root.rglob("*.yml"), *root.rglob("*.yaml"), *root.glob(".*.yml")]:
            load(path)
        for path in root.rglob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))


def test_workflows_pinned_and_least_privilege(rendered: dict[str, Path]) -> None:
    """B02/B30: SHA pins, empty top-level permissions, per-job grants, no main cancels."""
    for path in workflows(rendered):
        wf = load(path)
        assert wf.get("permissions") == {}, f"{path}: top-level permissions must be {{}}"
        for name, job in wf["jobs"].items():
            assert "permissions" in job, f"{path}: job {name} declares no permissions"
        group = wf.get("concurrency") or {}
        assert not (isinstance(group, dict) and group.get("cancel-in-progress") is True), path
        for step in steps(wf):
            uses = step.get("uses")
            if uses and not uses.startswith("./"):
                assert SHA.match(uses), f"{path}: '{uses}' not pinned to a commit SHA"
            if str(uses).startswith("actions/checkout@"):
                assert (step.get("with") or {}).get("persist-credentials") is False, path
            script = str(step.get("run", ""))
            assert not re.search(r"pip install (?![^\n]*==)", script), f"{path}: {script}"
            for m in re.finditer(r"uvx (\S+)", script):
                assert "@" in m.group(1), f"{path}: uvx {m.group(1)} has no version"


def test_codeql_uses_languages_input(rendered: dict[str, Path]) -> None:
    """B12: the init action reads `languages`; `language` is silently ignored."""
    wf = load(rendered["ts-py-go-all"] / ".github/workflows/codeql.yml")
    langs = wf["jobs"]["analyze"]["strategy"]["matrix"]["language"]
    assert langs == ["javascript-typescript", "python", "go", "actions"]
    for step in steps(wf):
        if "codeql-action/init" in str(step.get("uses", "")):
            assert "languages" in step["with"] and "language" not in step["with"]


def test_hooks_pinned_current_and_project_tools(rendered: dict[str, Path]) -> None:
    """B03/B27/B38: no archived mirrors; ruff and prettier come from the project lock."""
    hooks = load(rendered["ts-py-go-all"] / ".pre-commit-config.yaml")
    urls = {r["repo"] for r in hooks["repos"]}
    assert "https://github.com/pre-commit/mirrors-prettier" not in urls
    assert "https://github.com/astral-sh/ruff-pre-commit" not in urls
    for repo in hooks["repos"]:
        for hook in repo["hooks"]:
            for dep in hook.get("additional_dependencies", []):
                assert "==" in dep, f"hook {hook['id']}: '{dep}' not pinned"


def test_go_ratchet_where_lint_runs(rendered: dict[str, Path]) -> None:
    """B04/B26/B37: v2 config; ratchet in make lint; make check never writes."""
    root = rendered["ts-py-go-all"]
    cfg = load(root / ".golangci.yml")
    assert cfg["version"] == "2"
    assert "new-from-rev" not in (cfg.get("issues") or {})
    assert "prefix(example.com/x)" in cfg["formatters"]["settings"]["gci"]["sections"]
    make = (root / "hardening.mk").read_text(encoding="utf-8")
    assert "--new-from-rev=origin/main" in make and "fmt --diff" in make
    assert re.search(r"^check:.*fmt-check.*\$\(CHECK_LINT\)", make, re.MULTILINE)


def test_main_reports_debt_without_failing(rendered: dict[str, Path]) -> None:
    """B36/B37: PR scans are new-only; the default branch reports debt, never red."""
    wf = load(rendered["ts-py-go-all"] / ".github/workflows/hardening.yml")
    text = (rendered["ts-py-go-all"] / ".github/workflows/hardening.yml").read_text()
    assert "--log-opts=$BASE_SHA..HEAD" in text
    for step in steps(wf):
        if step.get("if") == "github.event_name != 'pull_request'":
            run_ = step.get("run", "")
            assert "--error" not in run_, step
            if "golangci-lint run" in run_:
                assert "--issues-exit-code=0" in run_


def test_codeowners_never_ships_a_live_placeholder(rendered: dict[str, Path]) -> None:
    """B21: a nonexistent owner makes GitHub skip the code-owner requirement."""
    blank = (rendered["ts-py-go-all"] / ".github/CODEOWNERS").read_text(encoding="utf-8")
    live = [ln for ln in blank.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    assert live == []
    owned = (rendered["py-owners"] / ".github/CODEOWNERS").read_text(encoding="utf-8")
    assert "*                          @acme/core" in owned
    assert "eslint-suppressions.json   @acme/core" in owned


def test_dal_directories_agree(rendered: dict[str, Path]) -> None:
    """B13: policy, ESLint rule and semgrep exempt the same directories."""
    root = rendered["ts-py-go-all"]
    rule = (root / "tools/hardening/no-raw-db-client.mjs").read_text(encoding="utf-8")
    semgrep = (root / ".semgrep/hardening.yml").read_text(encoding="utf-8")
    policy = (KIT / "DAL_POLICY.md").read_text(encoding="utf-8")
    for name in ("dal", "data-access", "data_access"):
        assert name in rule, name
        assert f"**/{name}/**" in semgrep, name
        assert f"`{name}/`" in policy, name


def test_docs_cite_only_real_rules() -> None:
    """B20: GOOGLE_GRADE.md must not promise rules the kit does not ship."""
    text = (KIT / "GOOGLE_GRADE.md").read_text(encoding="utf-8")
    assert "any-requires-justification" not in text
    assert "// WHY:" not in text
    assert "coverage gate |" not in text


def test_no_custom_ratchet_left() -> None:
    """B01/B05/B11/B22/B23/B34: the custom baseline ratchet is gone for good."""
    for path in KIT.joinpath("template").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            assert "skip-ratchet" not in text, path
            assert "raw-db-from.json" not in text, path
