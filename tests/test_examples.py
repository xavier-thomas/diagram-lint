"""Examples: the README shows `lint-before` failing and `lint-after` passing with the same
content, so these tests hold the example files to that claim.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "diagram-lint" / "scripts"))

import check_layout  # noqa: E402
import content_diff  # noqa: E402

BEFORE = str(ROOT / "examples" / "diagrams" / "lint-before.drawio")
AFTER = str(ROOT / "examples" / "diagrams" / "lint-after.drawio")


def test_before_reports_the_line_over_a_node_and_the_crossing() -> None:
    _, _, _, errs, unver, _ = check_layout.check(BEFORE)
    assert unver == []
    assert len(errs) == 2
    assert any("'Invoices' is drawn over node" in e for e in errs)
    assert any("'Writes' crosses" in e and "'Publishes'" in e for e in errs)


def test_after_is_clean() -> None:
    _, _, _, errs, unver, _ = check_layout.check(AFTER)
    assert errs == []
    assert unver == []


def test_before_and_after_have_the_same_content() -> None:
    assert content_diff.content(BEFORE) == content_diff.content(AFTER)
