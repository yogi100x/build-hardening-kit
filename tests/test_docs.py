"""Docs stay true: every relative link resolves, and every module has a page."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from harness import KIT

DOCS = sorted(
    p
    for p in [*KIT.glob("*.md"), *KIT.glob("docs/**/*.md"), *KIT.glob("tests/*.md")]
    if "fixtures" not in p.parts
)
LINK = re.compile(r"\]\(([^)\s]+)\)")


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: str(p.relative_to(KIT)))
def test_relative_links_resolve(doc: Path) -> None:
    for target in LINK.findall(doc.read_text(encoding="utf-8")):
        if re.match(r"^[a-z]+:", target) or target.startswith("#"):
            continue
        path = (doc.parent / target.split("#")[0]).resolve()
        assert path.exists(), f"{doc.relative_to(KIT)}: broken link {target}"


def test_every_module_has_a_page_and_a_readme_row() -> None:
    choices = yaml.safe_load((KIT / "copier.yml").read_text(encoding="utf-8"))["modules"]["choices"]
    readme = (KIT / "README.md").read_text(encoding="utf-8")
    for module in choices.values():
        assert (KIT / "docs/modules" / f"{module}.md").is_file(), module
        assert f"[`{module}`](docs/modules/{module}.md)" in readme, module
