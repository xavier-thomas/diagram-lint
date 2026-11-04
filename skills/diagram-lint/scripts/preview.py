#!/usr/bin/env python3
"""Render a rough SVG preview of a .drawio where draw.io is not installed.

    python3 scripts/preview.py file.drawio [...]   -> file.preview.svg

Shows node rectangles and pinned edge routes only, with no icons, line jumps or
rich text, so it does not replace the real render.
"""

# ruff: noqa: T201  CLI script; stdout is its interface
import html
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

from check_layout import parse, polyline, rect_of, style_dict


def text_lines(value: str | None) -> list[str]:
    v = re.sub(r"<br\s*/?>", "\n", value or "")
    v = re.sub(r"<[^>]+>", "", v)
    return [ln for ln in html.unescape(v).split("\n") if ln.strip()]


def render(path: str) -> pathlib.Path:
    nodes, boxes, edges = parse(path)
    ends = {**nodes, **boxes}
    root = ET.parse(path).getroot()
    gm = root.find(".//mxGraphModel")
    if gm is None:
        raise SystemExit(f"preview.py: {path} has no mxGraphModel; not a draw.io file")
    width = float(gm.get("pageWidth", 2000)) + 80
    height = float(gm.get("pageHeight", 1200)) + 80

    out = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="#fff"/>'
        ),
        (
            '<defs><marker id="a" markerWidth="10" markerHeight="7" refX="9" refY="3.5" '
            'orient="auto"><polygon points="0 0,10 3.5,0 7" fill="#555"/></marker></defs>'
        ),
    ]

    for cell in root.iter("mxCell"):
        geo = cell.find("mxGeometry")
        if cell.get("vertex") != "1" or geo is None:
            continue
        st = style_dict(cell.get("style"))
        x, y, w, h = rect_of(geo)
        x, y = x + 40, y + 40
        fill = st.get("fillColor", "#438DD5")
        boundary = fill == "none"
        stroke = st.get("strokeColor", "#2E6295")
        dash = ' stroke-dasharray="8 5"' if boundary or st.get("dashed") == "1" else ""
        out.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="{fill}" stroke="{stroke}"{dash}/>'
        )
        if "person2" in (st.get("shape") or ""):
            cx = x + w / 2
            out.append(
                f'<circle cx="{cx}" cy="{y + 18}" r="11" fill="#fff"/>'
                f'<path d="M{cx - 17},{y + 50} a17,17 0 0,1 34,0" fill="#fff"/>'
            )
        fc = "#444" if boundary else st.get("fontColor", "#fff")
        ty = y + (14 if boundary else float(st.get("spacingTop", 6)) + 10)
        for i, ln in enumerate(text_lines(cell.get("value"))[:5]):
            out.append(
                f'<text x="{x + w / 2}" y="{ty + i * 13}" font-family="Helvetica" '
                f'font-size="11" fill="{fc}" text-anchor="middle">'
                f"{html.escape(ln[:58])}</text>"
            )

    for e in edges:
        pl = polyline(e, ends)
        if pl is None:
            continue
        pts = " ".join(f"{p[0] + 40},{p[1] + 40}" for p in pl)
        col = e["style"].get("strokeColor", "#707070")
        dash = ' stroke-dasharray="6 4"' if e["style"].get("dashed") == "1" else ""
        out.append(
            f'<polyline points="{pts}" fill="none" stroke="{col}" '
            f'stroke-width="{e["style"].get("strokeWidth", "1.5")}"{dash} '
            f'marker-end="url(#a)"/>'
        )
        lines = text_lines(e["value"])
        mid = pl[len(pl) // 2]
        vertical = abs(pl[0][0] - pl[-1][0]) < 1
        for i, ln in enumerate(lines[:2]):
            tx = mid[0] + 40 + (52 if vertical else 0)
            ty2 = mid[1] + 40 + (i * 12) + (0 if vertical else -6 + i * 12)
            anchor_attr = "start" if vertical else "middle"
            out.append(
                f'<text x="{tx}" y="{ty2}" font-family="Helvetica" font-size="10" '
                f'fill="#333" text-anchor="{anchor_attr}">{html.escape(ln[:46])}</text>'
            )

    out.append("</svg>")
    dst = pathlib.Path(path).with_suffix(".preview.svg")
    dst.write_text("\n".join(out), encoding="utf-8", newline="\n")
    print(f"wrote {dst}")
    return dst


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        sys.stderr.write("usage: preview.py file.drawio [...]\n")
        return 2
    for f in argv[1:]:
        render(f)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
