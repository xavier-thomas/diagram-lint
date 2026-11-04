"""Generator: each pinned call must draw the route it was asked for, with the anchors that
make `check_layout` able to prove it.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "diagram-lint" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_layout  # noqa: E402
import drawio_lib as lib  # noqa: E402

Rect = tuple[float, float, float, float]
Point = tuple[float, float]

UPPER_LEFT: Rect = (0, 0, 100, 50)
LOWER_RIGHT: Rect = (300, 200, 100, 50)


def _drawn_route(doc: Any, tmp_path: Path) -> list[Point]:
    """The route that `check_layout` rebuilds from the file, for the document's only edge."""
    path = tmp_path / "t.drawio"
    doc.write(str(path))
    nodes, boxes, edges = check_layout.parse(str(path))
    route = check_layout.polyline(edges[0], {**nodes, **boxes})
    assert route is not None
    return route


def _doc(a_rect: Rect, b_rect: Rect) -> tuple[Any, str, str]:
    doc = lib.Doc("t")
    return (
        doc,
        doc.node("A", *a_rect, lib.S_CONT),
        doc.node("B", *b_rect, lib.S_CONT),
    )


def test_label_has_name_technology_and_description() -> None:
    assert lib.label("Web", "React", "Serves pages") == (
        "<b>Web</b><br/><i>[React]</i><br/><font style='font-size:10px'>Serves pages</font>"
    )


def test_label_leaves_out_empty_parts() -> None:
    assert lib.label("Web", "") == "<b>Web</b>"
    assert lib.label("Web", "React") == "<b>Web</b><br/><i>[React]</i>"


def test_label_escapes_its_text() -> None:
    assert lib.label("A & B", "<C>", "D > E") == (
        "<b>A &amp; B</b><br/><i>[&lt;C&gt;]</i><br/>"
        "<font style='font-size:10px'>D &gt; E</font>"
    )


def test_person_draws_the_person_icon_at_the_given_rectangle() -> None:
    doc = lib.Doc("t")
    person = doc.person("Analyst", 10, 20, 180, 160)
    assert doc.rects[person] == (10, 20, 180, 160)
    assert "shape=mxgraph.c4.person2" in doc.xml()


@pytest.mark.parametrize(
    ("a_rect", "b_rect", "corner", "first", "expected"),
    [
        pytest.param(
            UPPER_LEFT, LOWER_RIGHT, (50, 225), "v", [(50, 50), (50, 225), (300, 225)], id="v-down"
        ),
        pytest.param(
            LOWER_RIGHT, UPPER_LEFT, (350, 25), "v", [(350, 200), (350, 25), (100, 25)], id="v-up"
        ),
        pytest.param(
            UPPER_LEFT, LOWER_RIGHT, (350, 25), "h", [(100, 25), (350, 25), (350, 200)], id="h-out"
        ),
        pytest.param(
            LOWER_RIGHT, UPPER_LEFT, (50, 225), "h", [(300, 225), (50, 225), (50, 50)], id="h-back"
        ),
    ],
)
def test_elbow_leaves_and_enters_on_the_sides_facing_its_corner(
    a_rect: Rect,
    b_rect: Rect,
    corner: Point,
    first: str,
    expected: list[Point],
    tmp_path: Path,
) -> None:
    doc, a, b = _doc(a_rect, b_rect)
    doc.elbow(a, b, "bend", corner[0], corner[1], first=first)
    assert _drawn_route(doc, tmp_path) == expected


def test_elbow_rejects_an_unknown_first_leg() -> None:
    doc, a, b = _doc(UPPER_LEFT, LOWER_RIGHT)
    with pytest.raises(ValueError, match="first must be 'v' or 'h'"):
        doc.elbow(a, b, "bend", 50, 225, first="x")


ABOVE: Rect = (0, 0, 100, 50)
BELOW: Rect = (0, 200, 100, 50)
LEFT: Rect = (0, 100, 100, 50)
RIGHT: Rect = (300, 100, 100, 50)


@pytest.mark.parametrize(
    ("a_rect", "b_rect", "corners", "expected"),
    [
        pytest.param(
            ABOVE,
            BELOW,
            [(200, 25), (200, 225)],
            [(100, 25), (200, 25), (200, 225), (100, 225)],
            id="around-the-right",
        ),
        pytest.param(
            ABOVE,
            BELOW,
            [(-50, 25), (-50, 225)],
            [(0, 25), (-50, 25), (-50, 225), (0, 225)],
            id="around-the-left",
        ),
        pytest.param(
            LEFT,
            RIGHT,
            [(50, 40), (350, 40)],
            [(50, 100), (50, 40), (350, 40), (350, 100)],
            id="over-the-top",
        ),
        pytest.param(
            LEFT,
            RIGHT,
            [(50, 200), (350, 200)],
            [(50, 150), (50, 200), (350, 200), (350, 150)],
            id="under-the-bottom",
        ),
    ],
)
def test_route_picks_the_side_from_its_first_and_last_corners(
    a_rect: Rect,
    b_rect: Rect,
    corners: list[Point],
    expected: list[Point],
    tmp_path: Path,
) -> None:
    doc, a, b = _doc(a_rect, b_rect)
    doc.route(a, b, "detour", corners)
    assert _drawn_route(doc, tmp_path) == expected


def test_route_needs_a_corner() -> None:
    doc, a, b = _doc(UPPER_LEFT, LOWER_RIGHT)
    with pytest.raises(ValueError, match="at least one corner"):
        doc.route(a, b, "detour", [])


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(lambda d, a, b: d.elbow(a, b, "x", 50, 225, jump=True), id="elbow"),
        pytest.param(lambda d, a, b: d.route(a, b, "x", [(50, 225)], jump=True), id="route"),
    ],
)
def test_pinned_calls_pass_on_a_jump(call: Any) -> None:
    doc, a, b = _doc(UPPER_LEFT, LOWER_RIGHT)
    call(doc, a, b)
    assert "jumpStyle=arc" in doc.xml()


def test_label_pos_is_written_to_the_geometry() -> None:
    doc, a, b = _doc(ABOVE, BELOW)
    doc.vlink(a, b, "x", label_pos=-0.5)
    geometry = ET.fromstring(doc.xml()).find(".//mxCell[@edge='1']/mxGeometry")
    assert geometry is not None
    assert geometry.get("x") == "-0.5"
    assert geometry.find("mxPoint[@as='offset']") is not None


def test_edge_without_label_pos_or_points_has_a_bare_geometry() -> None:
    doc, a, b = _doc(ABOVE, BELOW)
    doc.edge(a, b)
    geometry = ET.fromstring(doc.xml()).find(".//mxCell[@edge='1']/mxGeometry")
    assert geometry is not None
    assert geometry.get("x") is None
    assert list(geometry) == []


def test_values_that_need_quoting_stay_well_formed() -> None:
    doc = lib.Doc('He said "hi" & <left>')
    a = doc.node('A "quoted" & <tagged>', 0, 0, 100, 50, lib.S_CONT)
    b = doc.node("B", 0, 200, 100, 50, lib.S_CONT)
    doc.vlink(a, b, '"x" & <y>')
    root = ET.fromstring(doc.xml())
    diagram = root.find("diagram")
    assert diagram is not None
    assert diagram.get("name") == 'He said "hi" & <left>'
    values = {cell.get("value") for cell in root.iter("mxCell")}
    assert {'A "quoted" & <tagged>', '"x" & <y>'} <= values


def test_page_size_is_written() -> None:
    model = ET.fromstring(lib.Doc("t", width=640, height=480).xml()).find(".//mxGraphModel")
    assert model is not None
    assert (model.get("pageWidth"), model.get("pageHeight")) == ("640", "480")


def test_write_creates_the_file_and_says_so(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc, _, _ = _doc(ABOVE, BELOW)
    path = tmp_path / "out.drawio"
    doc.write(str(path))
    assert path.read_text(encoding="utf-8") == doc.xml()
    assert str(path) in capsys.readouterr().out


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(lambda d, a, b: d.vlink(a, b, "x"), id="vlink"),
        pytest.param(lambda d, a, b: d.hlink(a, b, "x"), id="hlink"),
        pytest.param(lambda d, a, b: d.elbow(a, b, "x", 50, 225), id="elbow"),
        pytest.param(lambda d, a, b: d.route(a, b, "x", [(50, 225)]), id="route"),
    ],
)
def test_pinned_calls_add_no_jump_unless_asked(call: Any) -> None:
    doc, a, b = _doc(UPPER_LEFT, LOWER_RIGHT)
    call(doc, a, b)
    assert "jumpStyle" not in doc.xml()


# Away from the origin and of different sizes, so that no offset or size cancels out.
HIGH: Rect = (200, 100, 100, 50)
LOW: Rect = (200, 300, 100, 100)
NEAR: Rect = (100, 200, 50, 100)
FAR: Rect = (400, 250, 150, 100)


@pytest.mark.parametrize(
    ("a_rect", "b_rect", "lane", "expected"),
    [
        pytest.param(HIGH, LOW, None, [(250, 150), (250, 225), (250, 300)], id="down"),
        pytest.param(LOW, HIGH, None, [(250, 300), (250, 225), (250, 150)], id="up"),
        pytest.param(HIGH, LOW, 220, [(220, 150), (220, 225), (220, 300)], id="down-in-a-lane"),
    ],
)
def test_vlink_draws_one_vertical_through_the_gap(
    a_rect: Rect, b_rect: Rect, lane: float | None, expected: list[Point], tmp_path: Path
) -> None:
    doc, a, b = _doc(a_rect, b_rect)
    doc.vlink(a, b, "x", lane=lane)
    assert _drawn_route(doc, tmp_path) == expected


@pytest.mark.parametrize(
    ("a_rect", "b_rect", "lane", "expected"),
    [
        pytest.param(NEAR, FAR, None, [(150, 275), (275, 275), (400, 275)], id="rightwards"),
        pytest.param(FAR, NEAR, None, [(400, 275), (275, 275), (150, 275)], id="leftwards"),
        pytest.param(NEAR, FAR, 290, [(150, 290), (275, 290), (400, 290)], id="right-in-a-lane"),
    ],
)
def test_hlink_draws_one_horizontal_through_the_gap(
    a_rect: Rect, b_rect: Rect, lane: float | None, expected: list[Point], tmp_path: Path
) -> None:
    doc, a, b = _doc(a_rect, b_rect)
    doc.hlink(a, b, "x", lane=lane)
    assert _drawn_route(doc, tmp_path) == expected


ABOVE_AWAY: Rect = (1000, 1000, 100, 50)
BELOW_AWAY: Rect = (1000, 1200, 100, 50)
LEFT_AWAY: Rect = (1000, 1000, 100, 50)
RIGHT_AWAY: Rect = (1400, 1000, 100, 50)


@pytest.mark.parametrize(
    ("a_rect", "b_rect", "corners", "expected"),
    [
        pytest.param(
            ABOVE_AWAY,
            BELOW_AWAY,
            [(1050, 900), (1300, 900), (1300, 1225)],
            [(1050, 1000), (1050, 900), (1300, 900), (1300, 1225), (1100, 1225)],
            id="top-to-side-away-from-the-origin",
        ),
        pytest.param(
            ABOVE_AWAY,
            BELOW_AWAY,
            [(1300, 1025), (1300, 1300), (1050, 1300)],
            [(1100, 1025), (1300, 1025), (1300, 1300), (1050, 1300), (1050, 1250)],
            id="side-to-bottom-away-from-the-origin",
        ),
        pytest.param(
            LEFT_AWAY,
            RIGHT_AWAY,
            [(1000, 900), (1500, 900)],
            [(1000, 1000), (1000, 900), (1500, 900), (1500, 1000)],
            id="corners-on-the-outer-edges-count-as-within-the-width",
        ),
        pytest.param(
            LEFT_AWAY,
            RIGHT_AWAY,
            [(1100, 900), (1400, 900)],
            [(1100, 1000), (1100, 900), (1400, 900), (1400, 1000)],
            id="corners-on-the-inner-edges-count-as-within-the-width",
        ),
    ],
)
def test_route_anchors_are_relative_to_the_node(
    a_rect: Rect,
    b_rect: Rect,
    corners: list[Point],
    expected: list[Point],
    tmp_path: Path,
) -> None:
    doc, a, b = _doc(a_rect, b_rect)
    doc.route(a, b, "x", corners)
    assert _drawn_route(doc, tmp_path) == expected


def test_edge_returns_the_id_it_wrote() -> None:
    doc, a, b = _doc(ABOVE, BELOW)
    edge_id = doc.edge(a, b)
    assert ET.fromstring(doc.xml()).find(f".//mxCell[@id='{edge_id}']").get("edge") == "1"
