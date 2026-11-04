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
    assert "node differs:" in out
    assert "edge differs:" in out
    assert "box holds differs:" in out


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


def _edge_between(tmp_path: Path, name: str, src: str, dst: str, style: str = lib.S_EDGE) -> str:
    doc = lib.Doc("t")
    ids = {label: doc.node(label, 0, i * 100, 100, 50, lib.S_CONT) for i, label in enumerate("ABC")}
    doc.edge(ids[src], ids[dst], "uses", style)
    path = tmp_path / name
    doc.write(str(path))
    return str(path)


@pytest.mark.parametrize(
    ("after_src", "after_dst"),
    [
        pytest.param("B", "C", id="different-source"),
        pytest.param("A", "B", id="different-target"),
    ],
)
def test_reconnecting_one_end_of_an_edge_fails(
    after_src: str, after_dst: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before = _edge_between(tmp_path, "before.drawio", "A", "C")
    after = _edge_between(tmp_path, "after.drawio", after_src, after_dst)
    capsys.readouterr()
    assert content_diff.main(["content_diff.py", before, after]) == 1
    assert "edge differs:" in capsys.readouterr().out


def test_edges_are_keyed_by_their_labels_and_dash(tmp_path: Path) -> None:
    solid = _edge_between(tmp_path, "solid.drawio", "A", "B")
    dashed = _edge_between(tmp_path, "dashed.drawio", "A", "B", lib.S_EDGE_DASH)
    assert list(content_diff.content(solid)[1]) == [("A", "B", "uses", False)]
    assert list(content_diff.content(dashed)[1]) == [("A", "B", "uses", True)]


@pytest.mark.parametrize(
    ("centre_x", "centre_y", "inside"),
    [
        pytest.param(101, 200, True, id="just-inside-the-left-side"),
        pytest.param(100, 200, False, id="on-the-left-side"),
        pytest.param(299, 200, True, id="just-inside-the-right-side"),
        pytest.param(300, 200, False, id="on-the-right-side"),
        pytest.param(200, 101, True, id="just-inside-the-top-side"),
        pytest.param(200, 100, False, id="on-the-top-side"),
        pytest.param(200, 299, True, id="just-inside-the-bottom-side"),
        pytest.param(200, 300, False, id="on-the-bottom-side"),
    ],
)
def test_a_box_holds_the_nodes_whose_centre_is_inside(
    centre_x: float, centre_y: float, inside: bool, tmp_path: Path
) -> None:
    doc = lib.Doc("t")
    doc.node("Box", 100, 100, 200, 200, lib.S_BOUND)
    doc.node("N", centre_x - 50, centre_y - 25, 100, 50, lib.S_CONT)
    path = tmp_path / "t.drawio"
    doc.write(str(path))
    expected = ("Box", ("N",) if inside else ())
    assert list(content_diff.content(str(path))[2]) == [expected]
