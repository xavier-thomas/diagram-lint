#!/usr/bin/env python3
"""Check that two .drawio files say the same thing, whatever their layout.

    python3 scripts/content_diff.py before.drawio after.drawio

Compares node labels, edges (source, target, label, dashed) and the nodes whose
centre lies inside each boundary box. Ignores ids, anchors, waypoints and
coordinates. Exits 0 if equal, or 1 and prints every difference.
"""

# ruff: noqa: T201  CLI script; stdout is its interface
import html
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter

from check_layout import Rect, rect_of, style_dict

EdgeKey = tuple[str, str, str, bool]
BoxKey = tuple[str, tuple[str, ...]]


def plain(value: str | None) -> str:
    v = re.sub(r"<br\s*/?>", " / ", value or "")
    v = re.sub(r"<[^>]+>", "", v)
    return " ".join(html.unescape(v).split())


def content(path: str) -> tuple[Counter[str], Counter[EdgeKey], Counter[BoxKey]]:
    root = ET.parse(path).getroot()
    labels: dict[str, str] = {}
    rects: dict[str, Rect] = {}
    boxes: list[str] = []
    nodes: Counter[str] = Counter()
    edges: list[tuple[str | None, str | None, str, bool]] = []
    for cell in root.iter("mxCell"):
        cid = cell.get("id") or ""
        geo = cell.find("mxGeometry")
        if cell.get("vertex") == "1":
            labels[cid] = plain(cell.get("value"))
            nodes[labels[cid]] += 1
            if geo is not None:
                rects[cid] = rect_of(geo)
            if style_dict(cell.get("style")).get("fillColor") == "none":
                boxes.append(cid)
        elif cell.get("edge") == "1":
            st = style_dict(cell.get("style"))
            edges.append(
                (
                    cell.get("source"),
                    cell.get("target"),
                    plain(cell.get("value")),
                    st.get("dashed") == "1",
                )
            )
    keys: Counter[EdgeKey] = Counter()
    for src, dst, lab, dashed in edges:
        keys[(labels.get(src or "", "?"), labels.get(dst or "", "?"), lab, dashed)] += 1
    inside: Counter[BoxKey] = Counter()
    for b in boxes:
        bx, by, bw, bh = rects[b]
        held = sorted(
            labels[n]
            for n, (x, y, w, h) in rects.items()
            if n != b and n not in boxes and bx < x + w / 2 < bx + bw and by < y + h / 2 < by + bh
        )
        inside[(labels[b], tuple(held))] += 1
    return nodes, keys, inside


def report[K](kind: str, a: Counter[K], b: Counter[K]) -> bool:
    """Print every key whose count differs; True if any did."""
    bad = False
    for k in sorted(set(a) | set(b), key=str):
        if a[k] != b[k]:
            bad = True
            print(f"{kind} differs: {k!r}: before x{a[k]}, after x{b[k]}")
    return bad


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        sys.stderr.write("usage: content_diff.py before.drawio after.drawio\n")
        return 2
    n1, e1, b1 = content(argv[1])
    n2, e2, b2 = content(argv[2])
    if report("node", n1, n2) | report("edge", e1, e2) | report("box holds", b1, b2):
        return 1
    print(
        f"same content: {sum(n1.values())} nodes, {sum(e1.values())} edges, "
        f"{sum(b1.values())} boxes"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
