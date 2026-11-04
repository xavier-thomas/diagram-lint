#!/usr/bin/env python3
"""Check that a generated .drawio has no line over a node and no two lines crossing.

    python3 scripts/check_layout.py file.drawio [...]

Fails when an edge:

  1. passes through a node other than its own source and target
  2. crosses another edge, unless the later edge in file order draws a line jump
  3. lies on top of another edge
  4. has an anchor outside its node

Routes are rebuilt from pinned anchors and waypoints. A path whose segments are
all vertical or horizontal has only one possible route, so draw.io's router is
not modelled. Any other edge is reported as UNVERIFIED, never passed.
"""

# ruff: noqa: T201  CLI script; stdout is its interface
import sys
import xml.etree.ElementTree as ET
from itertools import combinations, pairwise, product
from typing import TypedDict

EPS = 1e-6
ANCHORS = ("exitX", "exitY", "entryX", "entryY")

Point = tuple[float, float]
Rect = tuple[float, float, float, float]


class Edge(TypedDict):
    id: str
    src: str | None
    dst: str | None
    pts: list[Point]
    style: dict[str, str]
    label: str
    value: str


Paths = dict[str, tuple[Edge, list[Point]]]


def style_dict(s: str | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in (s or "").split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def rect_of(geo: ET.Element) -> Rect:
    return (
        float(geo.get("x", 0)),
        float(geo.get("y", 0)),
        float(geo.get("width", 0)),
        float(geo.get("height", 0)),
    )


def parse(path: str) -> tuple[dict[str, Rect], dict[str, Rect], list[Edge]]:
    """Return the obstacle nodes, the boundary boxes and every edge."""
    root = ET.parse(path).getroot()
    nodes: dict[str, Rect] = {}
    boxes: dict[str, Rect] = {}
    edges: list[Edge] = []
    for cell in root.iter("mxCell"):
        cid = cell.get("id") or ""
        geo = cell.find("mxGeometry")
        if cell.get("vertex") == "1" and geo is not None:
            # An edge may end on a boundary box or cross it, so it is no obstacle.
            is_box = style_dict(cell.get("style")).get("fillColor") == "none"
            (boxes if is_box else nodes)[cid] = rect_of(geo)
        elif cell.get("edge") == "1":
            pts: list[Point] = []
            if geo is not None:
                arr = geo.find("Array")
                if arr is not None:
                    pts = [
                        (float(p.get("x", 0)), float(p.get("y", 0))) for p in arr.findall("mxPoint")
                    ]
            edges.append(
                {
                    "id": cid,
                    "src": cell.get("source"),
                    "dst": cell.get("target"),
                    "pts": pts,
                    "style": style_dict(cell.get("style")),
                    "label": (cell.get("value") or "")[:40],
                    "value": cell.get("value") or "",
                }
            )
    return nodes, boxes, edges


def endpoint(rect: Rect, sx: str, sy: str) -> Point:
    x, y, w, h = rect
    return (x + float(sx) * w, y + float(sy) * h)


def polyline(e: Edge, ends: dict[str, Rect]) -> list[Point] | None:
    """Return the route from pinned anchors and waypoints, or None if unpinned."""
    st = e["style"]
    src, dst = e["src"], e["dst"]
    if not all(k in st for k in ANCHORS) or src not in ends or dst not in ends:
        return None
    a = endpoint(ends[src], st["exitX"], st["exitY"])
    b = endpoint(ends[dst], st["entryX"], st["entryY"])
    return [a, *e["pts"], b]


# Half a pixel, because anchors stored as node fractions round-trip slightly off a lane.
TOL = 0.5


def axis_aligned(pl: list[Point]) -> bool:
    """Every segment is exactly vertical or exactly horizontal."""
    return all(abs(p[0] - q[0]) < TOL or abs(p[1] - q[1]) < TOL for p, q in pairwise(pl))


def merge_runs(pl: list[Point]) -> list[Point]:
    """Drop waypoints on a straight run of an axis-aligned path, keeping corners and reversals."""
    out = pl[:1]
    for q, r in pairwise(pl[1:]):
        p = out[-1]
        vertical = abs(p[0] - q[0]) < TOL and abs(q[0] - r[0]) < TOL
        horizontal = abs(p[1] - q[1]) < TOL and abs(q[1] - r[1]) < TOL
        same_way = (q[0] - p[0]) * (r[0] - q[0]) + (q[1] - p[1]) * (r[1] - q[1]) >= 0
        if not ((vertical or horizontal) and same_way):
            out.append(q)
    return [*out, *pl[-1:]]


def seg_rect_hit(p: Point, q: Point, rect: Rect) -> bool:
    """Does segment pq pass through the interior of rect? Sampled at 1 px."""
    x, y, w, h = rect
    x0, y0, x1, y1 = x, y, x + w, y + h
    n = max(2, int(max(abs(q[0] - p[0]), abs(q[1] - p[1]))))
    for i in range(n + 1):
        t = i / n
        cx, cy = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
        if x0 + 0.5 < cx < x1 - 0.5 and y0 + 0.5 < cy < y1 - 0.5:
            return True
    return False


def cross(o: Point, a: Point, b: Point) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def segments_cross(p1: Point, p2: Point, p3: Point, p4: Point) -> bool:
    d1, d2 = cross(p3, p4, p1), cross(p3, p4, p2)
    d3, d4 = cross(p1, p2, p3), cross(p1, p2, p4)
    return ((d1 > EPS and d2 < -EPS) or (d1 < -EPS and d2 > EPS)) and (
        (d3 > EPS and d4 < -EPS) or (d3 < -EPS and d4 > EPS)
    )


def segments_overlap(p1: Point, p2: Point, p3: Point, p4: Point) -> bool:
    """Collinear and sharing more than a point, judged along the first segment's axis."""
    if abs(cross(p1, p2, p3)) > 1e-3 or abs(cross(p1, p2, p4)) > 1e-3:
        return False
    axis = 0 if abs(p2[0] - p1[0]) >= abs(p2[1] - p1[1]) else 1
    lo1, hi1 = sorted((p1[axis], p2[axis]))
    lo2, hi2 = sorted((p3[axis], p4[axis]))
    return min(hi1, hi2) - max(lo1, lo2) >= 1.0


def draws_jump(e: Edge) -> bool:
    """Will draw.io draw a line jump on this edge? A curved edge also needs `curveGeometry=1`."""
    st = e["style"]
    if st.get("jumpStyle", "none") == "none":
        return False
    return st.get("curved") != "1" or st.get("curveGeometry") == "1"


def check(
    path: str,
) -> tuple[dict[str, Rect], list[Edge], Paths, list[str], list[str], list[str]]:
    nodes, boxes, edges = parse(path)
    ends = {**nodes, **boxes}
    errs: list[str] = []
    unver: list[str] = []
    jumps: list[str] = []
    paths: Paths = {}
    for e in edges:
        pl = polyline(e, ends)
        if pl is None:
            unver.append(
                f"{e['id']} {e['label']!r}: no pinned anchors, route is the router's choice"
            )
            continue
        for k in ANCHORS:
            f = float(e["style"][k])
            if not -0.001 <= f <= 1.001:
                errs.append(
                    f"{e['id']} {e['label']!r}: {k}={f:.3f} is outside the node. "
                    f"The lane misses the node it should attach to."
                )
        if not axis_aligned(pl):
            unver.append(
                f"{e['id']} {e['label']!r}: a segment between anchors and "
                f"waypoints is neither vertical nor horizontal, so the routed "
                f"path cannot be predicted"
            )
            continue
        paths[e["id"]] = (e, pl)

    for eid, (e, pl) in paths.items():
        for nid, rect in nodes.items():
            if nid not in (e["src"], e["dst"]) and any(
                seg_rect_hit(p, q, rect) for p, q in pairwise(pl)
            ):
                errs.append(f"{eid} {e['label']!r} is drawn over node {nid}")

    # Paths follow file order, so eb is the later edge, the one draw.io draws the jump on.
    for (ia, (ea, pa)), (ib, (eb, pb)) in combinations(paths.items(), 2):
        # Merged, because a crossing exactly at a waypoint is inside neither raw segment.
        for (p1, p2), (q1, q2) in product(pairwise(merge_runs(pa)), pairwise(merge_runs(pb))):
            if segments_cross(p1, p2, q1, q2):
                if draws_jump(eb):
                    msg = f"{ib} {eb['label']!r} jumps over {ia} {ea['label']!r}"
                    if msg not in jumps:
                        jumps.append(msg)
                else:
                    errs.append(f"{ia} {ea['label']!r} crosses {ib} {eb['label']!r}")
        for (p1, p2), (q1, q2) in product(pairwise(pa), pairwise(pb)):
            if segments_overlap(p1, p2, q1, q2):
                errs.append(f"{ia} {ea['label']!r} is drawn on top of {ib} {eb['label']!r}")
    return nodes, edges, paths, errs, unver, jumps


def main(argv: list[str]) -> int:
    files = argv[1:]
    if not files:
        sys.stderr.write("usage: check_layout.py file.drawio [...]\n")
        return 2
    bad = 0
    for f in files:
        nodes, edges, paths, errs, unver, jumps = check(f)
        print(
            f"\n{f}: {len(nodes)} nodes, {len(edges)} edges, "
            f"{len(paths)} verified, {len(unver)} unverifiable"
        )
        for u in unver:
            print(f"  UNVERIFIED  {u}")
        for j in jumps:
            print(f"  JUMP        {j} (intended)")
        for e in errs:
            print(f"  OVERLAP     {e}")
        if errs or unver:
            bad += 1
        else:
            print("  clean: no line over a node, no crossing, no line drawn on another")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
