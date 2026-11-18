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
ALL = ["format", "lint", "types", "secrets", "ci", "hooks", "governance", "agents", "arch-rules"]
RENDERS = {
    "ts-py-go-all": (["ts", "python", "go"], ALL, {"go_module": "example.com/x"}),
    "js-all": (["js"], ALL, {}),
    "py-owners": (["python"], ALL, {"code_owners": "@acme/core"}),
    "go-solo": (
        ["go"],
        ALL,
        {"code_owners": "@me", "required_reviews": "0", "require_codeql": "true"},
    ),
    "py-gov-no-ci": (["python"], ["secrets", "governance", "agents"], {}),
    "ts-minimal": (["ts"], None, {"preset": "minimal"}),
    "ts-pnpm": (["ts"], None, {"node_package_manager": "pnpm"}),
    "py-ci-only": (["python"], ["secrets", "ci"], {}),
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
        ".gitattributes",
        "AGENTS.md",
        "CLAUDE.md",
        ".github/pull_request_template.md",
        ".github/hardening/protect-branch.sh",
    ]:
        assert (full / rel).is_file(), rel
    minimal = rendered["ts-minimal"]
    for rel in [
        ".pre-commit-config.yaml",
        ".github/CODEOWNERS",
        "tools",
        ".semgrep",
        "AGENTS.md",
        ".github/hardening",
    ]:
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


def test_package_manager_follows_the_answer(rendered: dict[str, Path]) -> None:
    """Review finding: npm-only CI broke pnpm and yarn repos."""
    text = (rendered["ts-pnpm"] / ".github/workflows/hardening.yml").read_text()
    assert "pnpm install --frozen-lockfile" in text and "npm ci" not in text
    assert "cache: pnpm" in text
    npm = (rendered["ts-minimal"] / ".github/workflows/hardening.yml").read_text()
    assert "npm ci" in npm and "pnpm" not in npm


def test_no_check_step_without_check_modules(rendered: dict[str, Path]) -> None:
    """With only secrets + ci, there is no empty `check` to run."""
    root = rendered["py-ci-only"]
    assert "poe check" not in (root / ".github/workflows/hardening.yml").read_text()
    assert "[tasks.check]" not in (root / "poe_tasks.toml").read_text()


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
    # Only issues new since origin/main fail; with no such ref, all issues count.
    assert "origin/main" in make and "--new-from-rev=$(LINT_BASE)" in make
    assert "fmt --diff" in make
    assert "go build -o /dev/null ./..." in make  # no binary left in the repo
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


def protection(root: Path) -> dict:
    res = run([*tool("bash"), ".github/hardening/protect-branch.sh", "--dry-run"], root)
    assert res.ok, res.out
    return json.loads(res.out)


def job_check_names(job_id: str, job: dict) -> set[str]:
    """Names GitHub reports for a job: its `name` (else its id), with
    ${{ matrix.x }} expanded for every matrix value."""
    name = job.get("name", job_id)
    matrix = (job.get("strategy") or {}).get("matrix") or {}
    out = {name}
    for key, values in matrix.items():
        if isinstance(values, list):
            token = "${{ matrix." + key + " }}"
            out = {n.replace(token, str(v)) for n in out for v in values}
    return out


def reported_checks(root: Path, include_codeql: bool) -> set[str]:
    """Check names GitHub will report for the rendered workflows."""
    names: set[str] = set()
    files = ["hardening.yml"] + (["codeql.yml"] if include_codeql else [])
    for file in files:
        path = root / ".github/workflows" / file
        if path.exists():
            for job_id, job in load(path)["jobs"].items():
                names |= job_check_names(job_id, job)
    return names


@pytest.mark.parametrize(
    ("name", "codeql"),
    [
        ("ts-py-go-all", False),
        ("js-all", False),
        ("py-owners", False),
        ("go-solo", True),
        ("py-gov-no-ci", False),
    ],
)
def test_branch_protection_requires_exactly_the_real_checks(
    rendered: dict[str, Path], name: str, codeql: bool
) -> None:
    """A required check that never reports would block every merge forever."""
    root = rendered[name]
    body = protection(root)
    assert set(body["required_status_checks"]["contexts"]) == reported_checks(root, codeql)
    assert body["allow_force_pushes"] is False and body["enforce_admins"] is True


def test_protect_branch_arguments(rendered: dict[str, Path]) -> None:
    """Review finding: `owner/repo --dry-run` ran the real change."""
    root = rendered["py-owners"]
    script = [*tool("bash"), ".github/hardening/protect-branch.sh"]
    res = run([*script, "acme/app", "--dry-run"], root)
    assert res.ok and '"contexts"' in res.out, res.out
    res = run([*script, "--dry-rn"], root)
    assert res.code == 2 and "unknown option" in res.out


def test_workflows_run_in_merge_queue(rendered: dict[str, Path]) -> None:
    """Required checks must also report in a merge queue, or the queue deadlocks."""
    root = rendered["ts-py-go-all"]
    for file in ("hardening.yml", "codeql.yml"):
        on = load(root / ".github/workflows" / file)[True]  # YAML 1.1 reads `on` as True
        assert "merge_group" in on, file


def test_agents_md_names_only_real_commands(rendered: dict[str, Path]) -> None:
    """Review finding: AGENTS.md listed `poe check` with no check modules."""
    text = (rendered["py-gov-no-ci"] / "AGENTS.md").read_text(encoding="utf-8")
    assert "poe check" not in text and "`uv run poe test`" in text
    full = (rendered["ts-py-go-all"] / "AGENTS.md").read_text(encoding="utf-8")
    assert "`make check` — formatting, lint, types, vet, build" in full


def test_branch_protection_review_settings(rendered: dict[str, Path]) -> None:
    """Solo maintainers can set 0 reviews; owners are required only when real."""
    owned = protection(rendered["py-owners"])["required_pull_request_reviews"]
    assert owned == {
        "required_approving_review_count": 1,
        "require_code_owner_reviews": True,
        "dismiss_stale_reviews": True,
    }
    blank = protection(rendered["ts-py-go-all"])["required_pull_request_reviews"]
    assert blank["require_code_owner_reviews"] is False  # no owners named
    solo = protection(rendered["go-solo"])["required_pull_request_reviews"]
    assert solo["required_approving_review_count"] == 0
    assert solo["require_code_owner_reviews"] is False


def test_workflows_pass_actionlint_and_zizmor(rendered: dict[str, Path]) -> None:
    """Kit and rendered workflows: valid (actionlint) and no known-insecure patterns (zizmor)."""
    paths = [str(p) for p in workflows(rendered)]
    res = run([*tool("actionlint"), *paths], KIT)
    assert res.ok, res.out
    res = run([*tool("zizmor"), "--offline", "--min-severity", "low", *paths], KIT)
    assert res.ok, res.out


def test_no_custom_ratchet_left() -> None:
    """B01/B05/B11/B22/B23/B34: the custom baseline ratchet is gone for good."""
    for path in KIT.joinpath("template").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            assert "skip-ratchet" not in text, path
            assert "raw-db-from.json" not in text, path
