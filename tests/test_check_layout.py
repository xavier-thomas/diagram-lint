"""Verdicts: a route the check cannot predict is UNVERIFIED and fails, never clean, and a
line over a node fails unless that node is the line's own end or a boundary box.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "diagram-lint" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_layout  # noqa: E402
import drawio_lib as lib  # noqa: E402


def _run(
    doc: Any, tmp_path: Path, capsys: pytest.CaptureFixture[str], name: str = "t"
) -> tuple[int, str]:
    path = tmp_path / f"{name}.drawio"
    doc.write(str(path))
    capsys.readouterr()
    code = check_layout.main(["check_layout.py", str(path)])
    return code, capsys.readouterr().out


def _pair() -> tuple[Any, str, str]:
    """Two nodes that overlap neither horizontally nor vertically."""
    doc = lib.Doc("t")
    a = doc.node("A", 0, 0, 100, 50, lib.S_CONT)
    b = doc.node("B", 300, 200, 100, 50, lib.S_CONT)
    return doc, a, b


def test_edge_without_anchors_is_unverified_not_clean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc, a, b = _pair()
    doc.edge(a, b, "unpinned")
    code, out = _run(doc, tmp_path, capsys)
    assert code == 1
    assert "UNVERIFIED" in out and "'unpinned'" in out and "no pinned anchors" in out
    assert "clean" not in out


def test_edge_with_one_anchor_pair_missing_is_unverified(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc, a, b = _pair()
    doc.edge(a, b, "half", lib.S_EDGE + lib.anchor(exit_at=(1, 0.5)))
    code, out = _run(doc, tmp_path, capsys)
    assert code == 1
    assert "UNVERIFIED" in out


def test_diagonal_segment_is_unverified_not_clean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc, a, b = _pair()
    doc.edge(a, b, "diagonal", lib.S_EDGE + lib.anchor((1, 0.5), (0, 0.5)))
    code, out = _run(doc, tmp_path, capsys)
    assert code == 1
    assert "UNVERIFIED" in out and "neither vertical nor horizontal" in out
    assert "clean" not in out


def test_edge_to_a_missing_node_is_unverified(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc, a, _ = _pair()
    doc.edge(a, "gone", "dangling", lib.S_EDGE + lib.anchor((1, 0.5), (0, 0.5)))
    code, out = _run(doc, tmp_path, capsys)
    assert code == 1
    assert "UNVERIFIED" in out


def test_unverified_edge_does_not_hide_a_clean_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = lib.Doc("t")
    a = doc.node("A", 0, 0, 100, 50, lib.S_CONT)
    b = doc.node("B", 0, 200, 100, 50, lib.S_CONT)
    doc.vlink(a, b, "pinned")
    doc.edge(a, b, "unpinned")
    code, out = _run(doc, tmp_path, capsys)
    assert code == 1
    assert "2 edges, 1 verified, 1 unverifiable" in out


def test_lane_outside_the_node_reports_its_anchor(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = lib.Doc("t")
    a = doc.node("A", 0, 0, 100, 50, lib.S_CONT)
    b = doc.node("B", 0, 200, 100, 50, lib.S_CONT)
    doc.vlink(a, b, "stray", lane=500)
    code, out = _run(doc, tmp_path, capsys)
    assert code == 1
    assert "'stray': exitX=5.000 is outside the node" in out
    assert "'stray': entryX=5.000 is outside the node" in out


def test_anchor_on_the_node_edge_is_inside(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = lib.Doc("t")
    a = doc.node("A", 0, 0, 100, 50, lib.S_CONT)
    b = doc.node("B", 0, 200, 100, 50, lib.S_CONT)
    doc.vlink(a, b, "at the corner", lane=100)
    code, _ = _run(doc, tmp_path, capsys)
    assert code == 0


def _line_past_a_node(blocker_y: float) -> Any:
    """A horizontal lane at y=25 from A to C, past a node B between them."""
    doc = lib.Doc("t")
    a = doc.node("A", 0, 0, 100, 50, lib.S_CONT)
    doc.node("B", 300, blocker_y, 100, 50, lib.S_CONT)
    c = doc.node("C", 600, 0, 100, 50, lib.S_CONT)
    doc.hlink(a, c, "long", lane=25)
    return doc


def test_line_through_a_node_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out = _run(_line_past_a_node(0), tmp_path, capsys)
    assert code == 1
    assert "OVERLAP" in out and "'long' is drawn over node" in out
    assert "clean" not in out


def test_line_clear_of_a_node_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out = _run(_line_past_a_node(200), tmp_path, capsys)
    assert code == 0
    assert "clean" in out


def test_line_along_a_node_edge_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, _ = _run(_line_past_a_node(25), tmp_path, capsys)
    assert code == 0


def test_line_across_a_boundary_box_passes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = lib.Doc("t")
    doc.node("Boundary", 200, -100, 300, 300, lib.S_BOUND)
    a = doc.node("A", 0, 0, 100, 50, lib.S_CONT)
    b = doc.node("B", 600, 0, 100, 50, lib.S_CONT)
    doc.hlink(a, b, "across", lane=25)
    code, out = _run(doc, tmp_path, capsys)
    assert code == 0
    assert "2 nodes" in out


def test_edge_may_end_on_a_boundary_box(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    doc = lib.Doc("t")
    box = doc.node("Boundary", 200, 0, 300, 100, lib.S_BOUND)
    a = doc.node("A", 0, 0, 100, 100, lib.S_CONT)
    doc.hlink(a, box, "to the box", lane=50)
    code, out = _run(doc, tmp_path, capsys)
    assert code == 0
    assert "1 verified" in out


def test_one_bad_file_fails_the_run_and_every_file_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    good = tmp_path / "good.drawio"
    bad = tmp_path / "bad.drawio"
    _line_past_a_node(200).write(str(good))
    _line_past_a_node(0).write(str(bad))
    capsys.readouterr()
    code = check_layout.main(["check_layout.py", str(good), str(bad)])
    out = capsys.readouterr().out
    assert code == 1
    assert "good.drawio" in out and "bad.drawio" in out and "clean" in out and "OVERLAP" in out


def test_no_arguments_prints_usage(capsys: pytest.CaptureFixture[str]) -> None:
    assert check_layout.main(["check_layout.py"]) == 2
    assert "usage" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("p", "q", "rect"),
    [
        pytest.param((0, 10), (100, 10), (40, 0, 20, 20), id="horizontal-through-the-middle"),
        pytest.param((10, 0), (10, 100), (0, 40, 20, 20), id="vertical-through-the-middle"),
        pytest.param((-100, 10), (100, 10), (5, 5, 10, 10), id="horizontal-across-the-origin"),
        pytest.param((10, -100), (10, 100), (5, 5, 10, 10), id="vertical-across-the-origin"),
        pytest.param((0, 10), (100, 10), (98, 0, 10, 20), id="ending-just-inside"),
    ],
)
def test_segment_with_both_ends_outside_can_still_hit(
    p: check_layout.Point, q: check_layout.Point, rect: check_layout.Rect
) -> None:
    assert check_layout.seg_rect_hit(p, q, rect)


BOX: check_layout.Rect = (100, 100, 100, 100)


def _across_at_x(x: float) -> tuple[check_layout.Point, check_layout.Point]:
    return (x, 0), (x, 300)


def _across_at_y(y: float) -> tuple[check_layout.Point, check_layout.Point]:
    return (0, y), (300, y)


@pytest.mark.parametrize(
    "segment",
    [
        pytest.param(_across_at_x(100), id="on-the-left-side"),
        pytest.param(_across_at_x(100.5), id="half-a-pixel-inside-the-left-side"),
        pytest.param(_across_at_x(200), id="on-the-right-side"),
        pytest.param(_across_at_x(199.5), id="half-a-pixel-inside-the-right-side"),
        pytest.param(_across_at_y(100), id="on-the-top-side"),
        pytest.param(_across_at_y(100.5), id="half-a-pixel-inside-the-top-side"),
        pytest.param(_across_at_y(200), id="on-the-bottom-side"),
        pytest.param(_across_at_y(199.5), id="half-a-pixel-inside-the-bottom-side"),
    ],
)
def test_segment_within_the_tolerance_of_a_side_does_not_hit(
    segment: tuple[check_layout.Point, check_layout.Point],
) -> None:
    assert not check_layout.seg_rect_hit(*segment, BOX)


@pytest.mark.parametrize(
    "segment",
    [
        pytest.param(_across_at_x(101), id="inside-the-left-side"),
        pytest.param(_across_at_x(199), id="inside-the-right-side"),
        pytest.param(_across_at_y(101), id="inside-the-top-side"),
        pytest.param(_across_at_y(199), id="inside-the-bottom-side"),
    ],
)
def test_segment_past_the_tolerance_of_a_side_hits(
    segment: tuple[check_layout.Point, check_layout.Point],
) -> None:
    assert check_layout.seg_rect_hit(*segment, BOX)


@pytest.mark.parametrize(
    ("route", "expected"),
    [
        pytest.param([(0, 0), (0.4, 100)], True, id="vertical-within-half-a-pixel"),
        pytest.param([(0, 0), (0.5, 100)], False, id="vertical-at-half-a-pixel"),
        pytest.param([(0, 0), (100, 0.4)], True, id="horizontal-within-half-a-pixel"),
        pytest.param([(0, 0), (100, 0.5)], False, id="horizontal-at-half-a-pixel"),
    ],
)
def test_axis_aligned_allows_for_rounding_only(
    route: list[check_layout.Point], expected: bool
) -> None:
    assert check_layout.axis_aligned(route) is expected


@pytest.mark.parametrize(
    ("route", "expected"),
    [
        pytest.param(
            [(-100, 0), (-50, 0), (0, 0)], [(-100, 0), (0, 0)], id="forward-at-negative-x"
        ),
        pytest.param(
            [(0, -100), (0, -50), (0, 0)], [(0, -100), (0, 0)], id="forward-at-negative-y"
        ),
        pytest.param(
            [(-100, 0), (-50, 0), (-80, 0)], [(-100, 0), (-50, 0), (-80, 0)], id="reversal-in-x"
        ),
        pytest.param([(0, 0), (0, 0), (0, 50)], [(0, 0), (0, 50)], id="repeated-waypoint"),
        pytest.param([(0, 0), (0, 1), (0, 0.5)], [(0, 0), (0, 1), (0, 0.5)], id="small-reversal"),
        pytest.param(
            [(0, 0), (0.5, 50), (0.5, 100)],
            [(0, 0), (0.5, 50), (0.5, 100)],
            id="vertical-first-leg-off-by-half-a-pixel",
        ),
        pytest.param(
            [(0, 0), (0, 50), (0.5, 100)],
            [(0, 0), (0, 50), (0.5, 100)],
            id="vertical-second-leg-off-by-half-a-pixel",
        ),
        pytest.param(
            [(0, 0), (50, 0.5), (100, 0.5)],
            [(0, 0), (50, 0.5), (100, 0.5)],
            id="horizontal-first-leg-off-by-half-a-pixel",
        ),
        pytest.param(
            [(0, 0), (50, 0), (100, 0.5)],
            [(0, 0), (50, 0), (100, 0.5)],
            id="horizontal-second-leg-off-by-half-a-pixel",
        ),
    ],
)
def test_merge_runs_merges_only_straight_forward_runs(
    route: list[check_layout.Point], expected: list[check_layout.Point]
) -> None:
    assert check_layout.merge_runs(route) == expected


def test_cross_is_signed_by_turning_direction() -> None:
    assert check_layout.cross((0, 0), (1, 0), (0, 1)) == 1
    assert check_layout.cross((0, 0), (0, 1), (1, 0)) == -1


ACROSS = ((0, 0), (100, 0))


@pytest.mark.parametrize(
    ("other", "expected"),
    [
        pytest.param(((50, -50), (50, 50)), True, id="crossing"),
        pytest.param(((50, 10), (50, 50)), False, id="stopping-short"),
        pytest.param(((50, -50), (50, -10)), False, id="stopping-short-from-the-other-side"),
        pytest.param(((200, -50), (200, 50)), False, id="beyond-the-end"),
        pytest.param(((50, 0), (50, 50)), False, id="touching-from-one-side"),
    ],
)
def test_segments_cross_only_when_each_straddles_the_other(
    other: tuple[check_layout.Point, check_layout.Point], expected: bool
) -> None:
    assert check_layout.segments_cross(*ACROSS, *other) is expected
    assert check_layout.segments_cross(*other, *ACROSS) is expected
