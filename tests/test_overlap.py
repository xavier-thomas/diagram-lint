"""Overlap: two edges drawn along one line look like one line, and the check
must say so for horizontal and vertical runs alike.

`segments_overlap` once judged overlap on both axes, so two collinear
horizontal segments, whose y extent is zero, were never reported.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "diagram-lint" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_layout  # noqa: E402
import drawio_lib as lib  # noqa: E402


@pytest.mark.parametrize(
    ("a", "b", "c", "d"),
    [
        pytest.param((0, 0), (100, 0), (50, 0), (150, 0), id="horizontal-partial"),
        pytest.param((0, 0), (100, 0), (150, 0), (50, 0), id="horizontal-opposed"),
        pytest.param((0, 0), (100, 0), (20, 0), (80, 0), id="horizontal-contained"),
        pytest.param((5, 0), (5, 100), (5, 50), (5, 150), id="vertical-partial"),
        pytest.param((5, 100), (5, 0), (5, 50), (5, 150), id="vertical-opposed"),
        pytest.param((5, 0), (5, 100), (5, 20), (5, 80), id="vertical-contained"),
    ],
)
def test_collinear_overlapping_segments_overlap(
    a: check_layout.Point, b: check_layout.Point, c: check_layout.Point, d: check_layout.Point
) -> None:
    assert check_layout.segments_overlap(a, b, c, d)


@pytest.mark.parametrize(
    ("a", "b", "c", "d"),
    [
        pytest.param((0, 0), (100, 0), (100, 0), (200, 0), id="horizontal-touching"),
        pytest.param((0, 0), (100, 0), (150, 0), (250, 0), id="horizontal-apart"),
        pytest.param((5, 0), (5, 100), (5, 100), (5, 200), id="vertical-touching"),
        pytest.param((5, 0), (5, 100), (5, 150), (5, 250), id="vertical-apart"),
        pytest.param((0, 0), (100, 0), (0, 30), (100, 30), id="parallel-offset"),
        pytest.param((0, 0), (100, 0), (50, -50), (50, 50), id="perpendicular"),
    ],
)
def test_touching_apart_or_parallel_segments_do_not_overlap(
    a: check_layout.Point, b: check_layout.Point, c: check_layout.Point, d: check_layout.Point
) -> None:
    assert not check_layout.segments_overlap(a, b, c, d)


def _twin_edges(tmp_path: Path, *, vertical: bool, jump_second: bool) -> Path:
    """Two edges between the same pair of nodes, in the same lane."""
    doc = lib.Doc("t")
    if vertical:
        a = doc.node("A", 0, 0, 100, 50, lib.S_CONT)
        b = doc.node("B", 0, 300, 100, 50, lib.S_CONT)
        doc.vlink(a, b, "first", lane=50)
        doc.vlink(a, b, "second", lane=50, jump=jump_second)
    else:
        a = doc.node("A", 0, 0, 100, 100, lib.S_CONT)
        b = doc.node("B", 400, 0, 100, 100, lib.S_CONT)
        doc.hlink(a, b, "first", lane=50)
        doc.hlink(a, b, "second", lane=50, jump=jump_second)
    path = tmp_path / "t.drawio"
    doc.write(str(path))
    return path


@pytest.mark.parametrize("vertical", [False, True], ids=["horizontal", "vertical"])
def test_two_edges_in_one_lane_fail_the_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], vertical: bool
) -> None:
    path = _twin_edges(tmp_path, vertical=vertical, jump_second=False)
    code = check_layout.main(["check_layout.py", str(path)])
    out = capsys.readouterr().out
    assert code != 0
    assert "is drawn on top of" in out


@pytest.mark.parametrize("vertical", [False, True], ids=["horizontal", "vertical"])
def test_a_line_jump_does_not_excuse_an_overlap(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], vertical: bool
) -> None:
    path = _twin_edges(tmp_path, vertical=vertical, jump_second=True)
    code = check_layout.main(["check_layout.py", str(path)])
    out = capsys.readouterr().out
    assert code != 0
    assert "is drawn on top of" in out


@pytest.mark.parametrize(
    ("a", "b", "c", "d"),
    [
        pytest.param((200, 0), (200, 100), (200, 50), (200, 150), id="vertical-far-out"),
        pytest.param((0, 500), (100, 500), (50, 500), (150, 500), id="horizontal-far-out"),
        pytest.param((0, 0), (100, 0), (99, 0), (200, 0), id="sharing-one-pixel"),
    ],
)
def test_overlap_is_found_wherever_the_segments_are(
    a: check_layout.Point, b: check_layout.Point, c: check_layout.Point, d: check_layout.Point
) -> None:
    assert check_layout.segments_overlap(a, b, c, d)


@pytest.mark.parametrize(
    ("a", "b", "c", "d"),
    [
        pytest.param((0, 0), (100, 0), (99.5, 0), (200, 0), id="sharing-half-a-pixel"),
        pytest.param((0, 0), (100, 0), (20, 0), (80, 50), id="second-end-off-the-line"),
        pytest.param((0, 0), (100, 0), (20, 50), (80, 0), id="first-end-off-the-line"),
    ],
)
def test_short_or_diverging_segments_do_not_overlap(
    a: check_layout.Point, b: check_layout.Point, c: check_layout.Point, d: check_layout.Point
) -> None:
    assert not check_layout.segments_overlap(a, b, c, d)
