"""Line jumps: drawio_lib asks for one, check_layout accepts it only on the
later edge in file order.

Fixtures are generated here, not committed: a vertical lane A->B at x=50 and a
horizontal lane C->D at y=150 cross at (50, 150).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_layout  # noqa: E402


def _load_lib() -> Any:
    spec = importlib.util.spec_from_file_location("drawio_lib", SCRIPTS / "drawio_lib.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lib = _load_lib()


def _crossing(
    tmp_path: Path,
    *,
    jump_vertical: bool,
    jump_horizontal: bool,
    vertical_first: bool = True,
    x: float = 60,
    y: float = 150,
) -> Path:
    doc = lib.Doc("t")
    a = doc.node("A", 0, 0, 100, 50, lib.S_CONT)
    b = doc.node("B", 0, 300, 100, 50, lib.S_CONT)
    c = doc.node("C", -300, 100, 100, 100, lib.S_CONT)
    d = doc.node("D", 300, 100, 100, 100, lib.S_CONT)
    if vertical_first:
        doc.vlink(a, b, "v", lane=x, jump=jump_vertical)
        doc.hlink(c, d, "h", lane=y, jump=jump_horizontal)
    else:
        doc.hlink(c, d, "h", lane=y, jump=jump_horizontal)
        doc.vlink(a, b, "v", lane=x, jump=jump_vertical)
    path = tmp_path / "t.drawio"
    doc.write(str(path))
    return path


def _run(path: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = check_layout.main(["check_layout.py", str(path)])
    return code, capsys.readouterr().out


def test_edge_without_jump_has_no_jump_style() -> None:
    doc = lib.Doc("t")
    a = doc.node("A", 0, 0, 10, 10, lib.S_CONT)
    b = doc.node("B", 0, 100, 10, 10, lib.S_CONT)
    doc.edge(a, b)
    assert "jumpStyle" not in doc.xml()


def test_jump_true_writes_jump_style() -> None:
    doc = lib.Doc("t")
    a = doc.node("A", 0, 0, 10, 10, lib.S_CONT)
    b = doc.node("B", 0, 100, 10, 10, lib.S_CONT)
    doc.edge(a, b, jump=True)
    assert "jumpStyle=arc;jumpSize=" in doc.xml()


def test_crossing_without_jump_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _crossing(tmp_path, jump_vertical=False, jump_horizontal=False)
    code, out = _run(path, capsys)
    assert code != 0
    assert "crosses" in out


def test_jump_on_later_edge_passes_and_is_listed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _crossing(tmp_path, jump_vertical=False, jump_horizontal=True)
    code, out = _run(path, capsys)
    assert code == 0
    assert "JUMP" in out and "jumps over" in out


def test_jump_on_earlier_edge_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _crossing(tmp_path, jump_vertical=False, jump_horizontal=True, vertical_first=False)
    code, out = _run(path, capsys)
    assert code != 0
    assert "crosses" in out


# vlink's waypoint is at y=175 and hlink's at x=50, so these put a waypoint on the crossing.
WAYPOINT_ON_CROSSING = [(50, 150), (60, 175), (50, 175)]


@pytest.mark.parametrize(("x", "y"), WAYPOINT_ON_CROSSING)
def test_crossing_at_a_waypoint_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], x: float, y: float
) -> None:
    path = _crossing(tmp_path, jump_vertical=False, jump_horizontal=False, x=x, y=y)
    code, out = _run(path, capsys)
    assert code != 0
    assert "crosses" in out


@pytest.mark.parametrize(("x", "y"), WAYPOINT_ON_CROSSING)
def test_jump_at_a_waypoint_passes_and_is_listed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], x: float, y: float
) -> None:
    path = _crossing(tmp_path, jump_vertical=False, jump_horizontal=True, x=x, y=y)
    code, out = _run(path, capsys)
    assert code == 0
    assert "jumps over" in out


def test_edges_sharing_an_endpoint_do_not_cross(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = lib.Doc("t")
    a = doc.node("A", 0, 0, 100, 50, lib.S_CONT)
    b = doc.node("B", 0, 300, 100, 50, lib.S_CONT)
    c = doc.node("C", 300, 0, 100, 50, lib.S_CONT)
    doc.vlink(a, b, "v", lane=100)
    doc.hlink(a, c, "h", lane=50)
    path = tmp_path / "t.drawio"
    doc.write(str(path))
    code, _ = _run(path, capsys)
    assert code == 0


def test_merge_runs_drops_only_waypoints_on_a_straight_run() -> None:
    assert check_layout.merge_runs([(0, 0), (0, 50), (0, 100)]) == [(0, 0), (0, 100)]
    assert check_layout.merge_runs([(0, 0), (0, 50), (50, 50)]) == [(0, 0), (0, 50), (50, 50)]
    assert check_layout.merge_runs([(0, 0), (0, 50), (0, 20)]) == [(0, 0), (0, 50), (0, 20)]


def test_curved_jump_edge_needs_curve_geometry() -> None:
    edge: check_layout.Edge = {
        "id": "e",
        "src": None,
        "dst": None,
        "pts": [],
        "style": {"jumpStyle": "arc", "curved": "1"},
        "label": "",
        "value": "",
    }
    assert not check_layout.draws_jump(edge)
    edge["style"]["curveGeometry"] = "1"
    assert check_layout.draws_jump(edge)
