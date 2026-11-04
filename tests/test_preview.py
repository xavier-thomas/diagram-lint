"""Preview: a rough but valid SVG beside the source, drawing only what was pinned."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "diagram-lint" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import drawio_lib as lib  # noqa: E402
import preview  # noqa: E402

SVG = "{http://www.w3.org/2000/svg}"


def _render(doc: Any, tmp_path: Path) -> ET.Element:
    source = tmp_path / "d.drawio"
    doc.write(str(source))
    return ET.parse(preview.render(str(source))).getroot()


def _pair() -> tuple[Any, str, str]:
    doc = lib.Doc("t", width=640, height=480)
    return (
        doc,
        doc.node("A", 0, 0, 100, 50, lib.S_CONT),
        doc.node("B", 0, 200, 100, 50, lib.S_CONT),
    )


def _texts(svg: ET.Element) -> list[str]:
    return [t.text or "" for t in svg.iter(f"{SVG}text")]


def test_output_sits_beside_the_source_and_is_announced(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc, _, _ = _pair()
    source = tmp_path / "d.drawio"
    doc.write(str(source))
    capsys.readouterr()
    dst = preview.render(str(source))
    assert dst == tmp_path / "d.preview.svg"
    assert dst.exists()
    assert str(dst) in capsys.readouterr().out


def test_page_is_the_diagram_page_with_a_margin(tmp_path: Path) -> None:
    doc, _, _ = _pair()
    svg = _render(doc, tmp_path)
    assert (svg.get("width"), svg.get("height")) == ("720.0", "560.0")


def test_each_node_is_a_rectangle_offset_by_the_margin(tmp_path: Path) -> None:
    doc = lib.Doc("t")
    doc.node("A", 10, 20, 100, 50, lib.S_CONT)
    rects = list(_render(doc, tmp_path).iter(f"{SVG}rect"))
    background, node = rects
    assert background.get("fill") == "#fff"
    assert (node.get("x"), node.get("y")) == ("50.0", "60.0")
    assert (node.get("width"), node.get("height")) == ("100.0", "50.0")
    assert node.get("fill") == "#438DD5"
    assert node.get("stroke-dasharray") is None


@pytest.mark.parametrize(
    "style",
    [
        pytest.param(lib.S_BOUND, id="c4-boundary"),
        pytest.param("fillColor=none;strokeColor=#8C4FFF;dashed=0;", id="solid-group-stencil"),
    ],
)
def test_any_boundary_is_dashed_and_unfilled_with_dark_text(style: str, tmp_path: Path) -> None:
    doc = lib.Doc("t")
    doc.node("Boundary", 0, 0, 300, 300, style)
    svg = _render(doc, tmp_path)
    box = list(svg.iter(f"{SVG}rect"))[1]
    assert box.get("fill") == "none"
    assert box.get("stroke-dasharray") == "8 5"
    assert next(svg.iter(f"{SVG}text")).get("fill") == "#444"


def test_person_gets_a_head_and_other_nodes_do_not(tmp_path: Path) -> None:
    doc = lib.Doc("t")
    doc.person("Analyst", 0, 0, 180, 160)
    assert len(list(_render(doc, tmp_path).iter(f"{SVG}circle"))) == 1

    doc = lib.Doc("t")
    doc.node("A", 0, 0, 100, 50, lib.S_CONT)
    assert list(_render(doc, tmp_path).iter(f"{SVG}circle")) == []


def test_pinned_edge_is_drawn_along_its_route(tmp_path: Path) -> None:
    doc, a, b = _pair()
    doc.vlink(a, b, "uses")
    lines = list(_render(doc, tmp_path).iter(f"{SVG}polyline"))
    assert len(lines) == 1
    assert lines[0].get("points") == "90.0,90.0 90.0,165.0 90.0,240.0"
    assert lines[0].get("stroke-dasharray") is None


def test_dashed_edge_stays_dashed(tmp_path: Path) -> None:
    doc, a, b = _pair()
    doc.vlink(a, b, "uses", lib.S_EDGE_DASH)
    line = next(_render(doc, tmp_path).iter(f"{SVG}polyline"))
    assert line.get("stroke-dasharray") == "6 4"


def test_unpinned_edge_is_left_out(tmp_path: Path) -> None:
    doc, a, b = _pair()
    doc.edge(a, b, "unpinned")
    svg = _render(doc, tmp_path)
    assert list(svg.iter(f"{SVG}polyline")) == []
    assert "unpinned" not in _texts(svg)


@pytest.mark.parametrize(
    ("link", "anchor"),
    [
        pytest.param("vlink", "start", id="beside-a-vertical-edge"),
        pytest.param("hlink", "middle", id="centred-on-a-horizontal-edge"),
    ],
)
def test_edge_label_placement(link: str, anchor: str, tmp_path: Path) -> None:
    doc = lib.Doc("t")
    a = doc.node("A", 0, 0, 100, 100, lib.S_CONT)
    b = doc.node("B", *((0, 300) if link == "vlink" else (300, 0)), 100, 100, lib.S_CONT)
    getattr(doc, link)(a, b, "uses")
    labels = [t for t in _render(doc, tmp_path).iter(f"{SVG}text") if t.text == "uses"]
    assert len(labels) == 1
    assert labels[0].get("text-anchor") == anchor


def test_label_markup_becomes_separate_lines(tmp_path: Path) -> None:
    doc = lib.Doc("t")
    doc.node(lib.label("Web", "React", "Serves pages"), 0, 0, 200, 100, lib.S_CONT)
    assert _texts(_render(doc, tmp_path)) == ["Web", "[React]", "Serves pages"]


def test_special_characters_stay_well_formed(tmp_path: Path) -> None:
    doc, a, b = _pair()
    doc.vlink(a, b, "reads &amp; &lt;writes&gt;")
    doc.node(lib.label("A & B", "<C>"), 300, 0, 100, 50, lib.S_CONT)
    texts = _texts(_render(doc, tmp_path))
    assert {"A & B", "[<C>]", "reads & <writes>"} <= set(texts)


def test_long_labels_are_cut_short(tmp_path: Path) -> None:
    doc = lib.Doc("t")
    lines = "<br/>".join(f"line {i}" for i in range(9))
    doc.node(lines, 0, 0, 100, 50, lib.S_CONT)
    doc.node("x" * 80, 300, 0, 100, 50, lib.S_CONT)
    texts = _texts(_render(doc, tmp_path))
    assert [t for t in texts if t.startswith("line")] == [f"line {i}" for i in range(5)]
    assert "x" * 58 in texts


def test_file_without_a_graph_model_is_refused(tmp_path: Path) -> None:
    source = tmp_path / "not.drawio"
    source.write_text("<mxfile/>", encoding="utf-8")
    with pytest.raises(SystemExit, match=r"not a draw\.io file"):
        preview.render(str(source))


def _text_at(svg: ET.Element, text: str) -> tuple[str | None, str | None]:
    found = next(t for t in svg.iter(f"{SVG}text") if t.text == text)
    return found.get("x"), found.get("y")


def test_node_text_is_centred_and_stacked_from_the_top(tmp_path: Path) -> None:
    doc = lib.Doc("t")
    doc.node(lib.label("Web", "React"), 10, 20, 100, 50, lib.S_CONT)
    svg = _render(doc, tmp_path)
    assert _text_at(svg, "Web") == ("100.0", "76.0")
    assert _text_at(svg, "[React]") == ("100.0", "89.0")


def test_boundary_title_sits_at_the_top(tmp_path: Path) -> None:
    doc = lib.Doc("t")
    doc.node("Boundary", 0, 0, 300, 300, lib.S_BOUND)
    assert _text_at(_render(doc, tmp_path), "Boundary") == ("190.0", "54.0")


def test_person_head_and_shoulders_are_centred(tmp_path: Path) -> None:
    doc = lib.Doc("t")
    doc.person("Analyst", 0, 0, 180, 160)
    svg = _render(doc, tmp_path)
    head = next(svg.iter(f"{SVG}circle"))
    assert (head.get("cx"), head.get("cy")) == ("130.0", "58.0")
    assert next(svg.iter(f"{SVG}path")).get("d", "").startswith("M113.0,90.0 ")


def test_edge_label_sits_beside_a_vertical_edge(tmp_path: Path) -> None:
    doc = lib.Doc("t")
    a = doc.node("A", 0, 0, 100, 100, lib.S_CONT)
    b = doc.node("B", 0, 300, 100, 100, lib.S_CONT)
    doc.vlink(a, b, "first<br/>second")
    svg = _render(doc, tmp_path)
    assert _text_at(svg, "first") == ("142.0", "240.0")
    assert _text_at(svg, "second") == ("142.0", "252.0")


def test_edge_label_straddles_a_horizontal_edge(tmp_path: Path) -> None:
    doc = lib.Doc("t")
    a = doc.node("A", 0, 0, 100, 100, lib.S_CONT)
    b = doc.node("B", 300, 0, 100, 100, lib.S_CONT)
    doc.hlink(a, b, "above<br/>below")
    svg = _render(doc, tmp_path)
    assert _text_at(svg, "above") == ("240.0", "84.0")
    assert _text_at(svg, "below") == ("240.0", "108.0")


def test_main_renders_every_file(tmp_path: Path) -> None:
    doc, _, _ = _pair()
    one = tmp_path / "one.drawio"
    two = tmp_path / "two.drawio"
    doc.write(str(one))
    doc.write(str(two))
    assert preview.main(["preview.py", str(one), str(two)]) == 0
    assert (tmp_path / "one.preview.svg").exists()
    assert (tmp_path / "two.preview.svg").exists()


def test_main_renders_a_single_file(tmp_path: Path) -> None:
    doc, _, _ = _pair()
    source = tmp_path / "only.drawio"
    doc.write(str(source))
    assert preview.main(["preview.py", str(source)]) == 0
    assert (tmp_path / "only.preview.svg").exists()


def test_main_without_files_prints_usage(capsys: pytest.CaptureFixture[str]) -> None:
    assert preview.main(["preview.py"]) == 2
    assert "usage" in capsys.readouterr().err
