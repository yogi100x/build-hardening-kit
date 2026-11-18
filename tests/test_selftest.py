"""Install each variant into a fixture repo and prove its gate means something.

For every stack:
  * clean: right after install, exactly the steps listed in known_bugs.CLEAN_RED
    are red (none, once the kit is healthy);
  * every planted case gets its expected outcome: a violation is caught by the
    step meant to catch it, with that rule's own message in the output; a
    legitimate change (must_pass) is accepted.

Known bugs are listed with ids in tests/KNOWN_BUGS.md and their exact outcomes
in tests/known_bugs.py. Any difference from the recorded outcome fails the run,
whether a bug was fixed (update the entry) or something new broke.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from harness import Repo, make_repo, publish_main, tool
from known_bugs import expected_case, expected_clean
from stacks import STACKS, caught, run_gate

Installed = tuple[str, Repo, dict[str, str]]


@pytest.fixture(scope="module")
def installed(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Installed:
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
    clean_failures = run_gate(stack, repo)
    repo.reset()  # hooks may have rewritten files; start every case from main
    return name, repo, clean_failures


def cases() -> list[tuple[str, str]]:
    out = []
    for name, stack in sorted(STACKS.items()):
        out.append((name, "clean"))
        out.extend((name, case) for case in stack.cases)
    return out


@pytest.mark.parametrize(
    ("installed", "case"),
    cases(),
    ids=[f"{s}-{c}" for s, c in cases()],
    indirect=["installed"],
)
def test_gate(installed: Installed, case: str) -> None:
    stack_name, repo, clean_failures = installed
    stack = STACKS[stack_name]

    if case == "clean":
        # Entry points (npm run check, uv run poe check, make check) count here.
        expected = expected_clean(stack_name)
        unexpected = {k: v for k, v in clean_failures.items() if k not in expected}
        fixed = sorted(set(expected) - set(clean_failures))
        assert not unexpected, "steps red on a clean install that no known bug explains:\n" + (
            "\n".join(f"--- {label} ---\n{out}" for label, out in unexpected.items())
        )
        assert not fixed, (
            f"steps now green on clean: {fixed}; remove them from known_bugs.CLEAN_RED"
        )
        return

    c = stack.cases[case]
    labels = {label for label, _, _ in stack.gate}
    usable = (c.steps & labels) - clean_failures.keys()
    if not usable:
        outcome, detail = (
            "blocked",
            (
                f"expected steps {sorted(c.steps)}: absent={sorted(c.steps - labels)}, "
                f"red on clean={sorted(c.steps & clean_failures.keys())}"
            ),
        )
    else:
        try:
            repo.plant(c.files)
            failures = run_gate(stack, repo, only=usable, env=c.env)
        finally:
            repo.reset()
        if c.must_pass:
            outcome = "false-alarm" if failures else "ok"
        else:
            outcome = "caught" if caught(c, failures) else "missed"
        detail = "\n".join(f"--- {label} ---\n{out}" for label, out in failures.items())

    healthy = "ok" if c.must_pass else "caught"
    want, bug = expected_case(stack_name, case, healthy)
    assert outcome == want, (
        f"{stack_name}/{case}: outcome '{outcome}', recorded '{want}'"
        + (f" ({bug})" if bug else "")
        + ("; if a bug was fixed, update tests/known_bugs.py" if bug else "")
        + f"\n{detail}"
    )


def test_fixtures_exist() -> None:
    for stack in STACKS.values():
        assert (Path(__file__).parent / "fixtures" / stack.fixture).is_dir(), stack.fixture
