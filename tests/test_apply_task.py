"""Unit tests for tasks/apply.py helpers that the fixture runs cannot isolate."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from harness import KIT

spec = importlib.util.spec_from_file_location("apply", KIT / "tasks" / "apply.py")
assert spec and spec.loader
apply = importlib.util.module_from_spec(spec)
spec.loader.exec_module(apply)


def test_dev_dependencies_reads_only_what_uv_sync_installs() -> None:
    """Review finding: a tool listed only as an optional extra counted as present."""
    text = (
        '[project]\nname = "x"\noptional-dependencies = { dev = ["ruff", "mypy"] }\n\n'
        '[dependency-groups]\ndev = ["pytest>=8", "Poethepoet[poetry_plugin]"]\n\n'
        '[tool.uv]\ndev-dependencies = ["mypy_extensions==1.0"]\n'
    )
    assert apply.dev_dependencies(text) == {"pytest", "poethepoet", "mypy-extensions"}


def test_known_scripts_cover_every_module_combination() -> None:
    known = apply.known_kit_scripts()
    assert "npm run lint" in known["check"]
    assert "npm run format:check && npm run typecheck" in known["check"]
    assert known["typecheck"] == {"tsc --noEmit", "tsc --noEmit -p jsconfig.json"}


def test_package_json_written_with_lf(tmp_path: Path) -> None:
    """Review finding: on Windows, write_text turned \\n into \\r\\n."""
    path = tmp_path / "package.json"
    apply.write_lf(path, '{\n  "a": 1\n}\n')
    assert b"\r\n" not in path.read_bytes()
