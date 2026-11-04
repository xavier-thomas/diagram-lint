"""Content: a re-layout may move anything, but any change to what the diagram says must show."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "diagram-lint" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import content_diff  # noqa: E402
import drawio_lib as lib  # noqa: E402


def _doc(
    *,
    a_label: str = "A",
    a_x: float = 100,
    b_x: float = 100,
    edge_label: str = "uses",
    edge_style: str | None = None,
    reverse: bool = False,
    extra_edge: bool = False,
    lane: float | None = None,
) -> Any:
    """Node A inside a boundary box, with an edge to node B below the box."""
    doc = lib.Doc("t")
    doc.node("Boundary", 0, 0, 400, 200, lib.S_BOUND)
    a = doc.node(a_label, a_x, 50, 100, 50, lib.S_CONT)
    b = doc.node("B", b_x, 300, 100, 50, lib.S_CONT)
    first, second = (b, a) if reverse else (a, b)
    doc.edge(first, second, edge_label, edge_style or lib.S_EDGE)
    if extra_edge:
        doc.edge(first, second, edge_label, edge_style or lib.S_EDGE)
    if lane is not None:
        doc.vlink(a, b, "pinned", lane=lane)
    return doc


def _diff(
    before: Any, after: Any, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> tuple[int, str]:
    first = tmp_path / "before.drawio"
    second = tmp_path / "after.drawio"
    before.write(str(first))
    after.write(str(second))
    capsys.readouterr()
    code = content_diff.main(["content_diff.py", str(first), str(second)])
    return code, capsys.readouterr().out


@pytest.mark.parametrize(
    "make_after",
    [
        pytest.param(lambda: _doc(), id="identical"),
        pytest.param(lambda: _doc(a_x=250, b_x=600), id="moved-without-leaving-the-box"),
        pytest.param(lambda: _doc(a_label="<b>A</b>"), id="markup-only"),
        pytest.param(lambda: _doc(a_label="  A  "), id="whitespace-only"),
    ],
)
def test_same_content_passes(
    make_after: Callable[[], Any], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _diff(_doc(), make_after(), tmp_path, capsys)
    assert code == 0
    assert out.startswith("same content: 3 nodes, 1 edges, 1 boxes")


def test_anchors_and_waypoints_are_ignored(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, _ = _diff(_doc(lane=120), _doc(lane=180), tmp_path, capsys)
    assert code == 0


@pytest.mark.parametrize(
    ("make_after", "expected"),
    [
        pytest.param(lambda: _doc(a_label="Renamed"), "node differs: 'Renamed'", id="node-label"),
        pytest.param(lambda: _doc(edge_label="calls"), "edge differs:", id="edge-label"),
        pytest.param(lambda: _doc(reverse=True), "edge differs:", id="edge-direction"),
        pytest.param(lambda: _doc(extra_edge=True), "before x1, after x2", id="edge-count"),
        pytest.param(lambda: _doc(edge_style=lib.S_EDGE_DASH), "edge differs:", id="edge-dashed"),
        pytest.param(lambda: _doc(a_x=600), "box holds differs:", id="node-left-the-box"),
        pytest.param(lambda: _doc(lane=120), "edge differs:", id="edge-added"),
    ],
)
def test_changed_content_fails_and_says_what_changed(
    make_after: Callable[[], Any],
    expected: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out = _diff(_doc(), make_after(), tmp_path, capsys)
    assert code == 1
    assert expected in out
    assert "same content" not in out


def test_every_difference_is_printed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out = _diff(_doc(), _doc(a_label="Renamed", edge_label="calls"), tmp_path, capsys)
    assert code == 1
    assert "node differs:" in out and "edge differs:" in out and "box holds differs:" in out


def test_line_breaks_in_a_label_count_as_a_separator() -> None:
    assert content_diff.plain("<b>Web</b><br/><i>[React]</i>") == "Web / [React]"
    assert content_diff.plain("A &amp; B") == "A & B"
    assert content_diff.plain(None) == ""


@pytest.mark.parametrize("argv", [["content_diff.py"], ["content_diff.py", "only-one.drawio"]])
def test_wrong_argument_count_prints_usage(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    assert content_diff.main(argv) == 2
    assert "usage" in capsys.readouterr().err
