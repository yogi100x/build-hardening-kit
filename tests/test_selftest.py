"""Install each variant into a fixture repo and prove its gate means something.

For every stack:
  * clean: the gate passes on the untouched fixture right after install;
  * every planted violation makes the gate fail.

Known kit bugs are listed in tests/known_bugs.py. A case marked there is an
expected failure; once the bug is fixed the case passes, pytest reports XPASS,
and (xfail_strict) the run fails until the marker is removed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from harness import Repo, make_repo, publish_main, tool
from known_bugs import expected_failure
from stacks import STACKS, gate_failures


@pytest.fixture(scope="module")
def installed(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> tuple[str, Repo, dict[str, str]]:
    name: str = request.param
    stack = STACKS[name]
    for t in stack.tools:
        tool(t)
    repo = make_repo(stack.fixture, tmp_path_factory.mktemp(name))
    try:
        for step in stack.setup:
            step(repo)
    except RuntimeError as exc:
        pytest.fail(f"[{name}] setup failed: {exc}")
    repo.commit_all("install build-hardening-kit")
    publish_main(repo)
    return name, repo, gate_failures(stack, repo)


def cases() -> list[tuple[str, str]]:
    out = []
    for name, stack in sorted(STACKS.items()):
        out.append((name, "clean"))
        out.extend((name, case) for case in stack.violations)
    return out


@pytest.mark.parametrize(
    ("installed", "case"), cases(), ids=[f"{s}-{c}" for s, c in cases()], indirect=["installed"]
)
def test_gate(
    installed: tuple[str, Repo, dict[str, str]], case: str, request: pytest.FixtureRequest
) -> None:
    stack_name, repo, clean_failures = installed
    bug = expected_failure(stack_name, case)
    if bug:
        request.applymarker(pytest.mark.xfail(reason=bug, strict=True))
    stack = STACKS[stack_name]
    if case == "clean":
        assert not clean_failures, "gate fails on a clean install:\n" + "\n".join(
            f"--- {label} ---\n{out}" for label, out in clean_failures.items()
        )
        return
    v = stack.violations[case]
    labels = {label for label, _, _ in stack.gate}
    usable = (v.caught_by & labels) - clean_failures.keys()
    assert usable, (
        f"no usable step for '{case}': expected one of {sorted(v.caught_by)}; "
        f"present={sorted(labels & v.caught_by)}, red on clean={sorted(clean_failures.keys() & v.caught_by)}"
    )
    try:
        repo.plant(v.files)
        failures = gate_failures(stack, repo, env=v.env)
    finally:
        repo.reset()
    assert usable & failures.keys(), f"planted '{case}' violation not caught by {sorted(usable)}"


def test_fixtures_exist() -> None:
    for stack in STACKS.values():
        assert (Path(__file__).parent / "fixtures" / stack.fixture).is_dir(), stack.fixture
