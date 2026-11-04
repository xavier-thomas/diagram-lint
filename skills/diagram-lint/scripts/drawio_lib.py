#!/usr/bin/env python3
"""The draw.io generator library: C4 styles, `label()`, `anchor()` and `Doc`.

Usage and layout rules: `references/drawio.md` in this skill.
"""

# ruff: noqa: T201  CLI script; stdout is its interface
from html import escape
from xml.sax.saxutils import quoteattr

Point = tuple[float, float]
Rect = tuple[float, float, float, float]

# C4 palette
S_PERSON = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#08427B;strokeColor=#052E56;"
    "fontColor=#FFFFFF;verticalAlign=top;spacingTop=6;fontSize=11;"
)
S_SYSTEM = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#1168BD;strokeColor=#0B4884;"
    "fontColor=#FFFFFF;verticalAlign=top;spacingTop=6;fontSize=11;"
)
S_CONT = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#438DD5;strokeColor=#2E6295;"
    "fontColor=#FFFFFF;verticalAlign=top;spacingTop=6;fontSize=11;"
)
S_DB = (
    "shape=cylinder3;boundedLbl=1;backgroundOutline=1;whiteSpace=wrap;html=1;"
    "fillColor=#438DD5;strokeColor=#2E6295;fontColor=#FFFFFF;fontSize=11;"
)
S_EXT = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#999999;strokeColor=#6B6B6B;"
    "fontColor=#FFFFFF;verticalAlign=top;spacingTop=6;fontSize=11;"
)
# Unknown stencil names render blank, so render any replacement and inspect it.
# aspect=fixed stops a wide, short box squashing the icon into an oval.
S_PERSON_ICON = (
    "shape=mxgraph.c4.person2;html=1;whiteSpace=wrap;fillColor=#08427B;"
    "strokeColor=#052E56;fontColor=#FFFFFF;align=center;"
    "verticalAlign=top;spacingTop=54;fontSize=11;aspect=fixed;"
)
S_BOUND = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#444444;"
    "dashed=1;verticalAlign=top;fontStyle=1;fontSize=13;fontColor=#444444;"
)
S_EDGE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;fontSize=10;"
    "strokeColor=#707070;fontColor=#404040;endArrow=blockThin;endFill=1;"
)
S_EDGE_HL = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;fontSize=10;"
    "strokeColor=#1B7B1B;fontColor=#1B7B1B;strokeWidth=2;"
    "endArrow=blockThin;endFill=1;"
)
S_EDGE_DASH = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;fontSize=10;dashed=1;"
    "strokeColor=#8A8A8A;fontColor=#606060;endArrow=blockThin;endFill=1;"
)


JUMP_SIZE = 8


def label(title: str, tech: str, desc: str = "") -> str:
    """Build a C4 HTML label: bold name, italic technology, plain description."""
    out = f"<b>{escape(title)}</b>"
    if tech:
        out += f"<br/><i>[{escape(tech)}]</i>"
    if desc:
        out += f"<br/><font style='font-size:10px'>{escape(desc)}</font>"
    return out


def anchor(exit_at: Point | None = None, entry_at: Point | None = None) -> str:
    """Build the style that pins where an edge leaves and enters its nodes."""
    s = ""
    if exit_at:
        s += f"exitX={exit_at[0]};exitY={exit_at[1]};exitDx=0;exitDy=0;"
    if entry_at:
        s += f"entryX={entry_at[0]};entryY={entry_at[1]};entryDx=0;entryDy=0;"
    return s


class Doc:
    def __init__(self, name: str, width: int = 1600, height: int = 1200) -> None:
        self.name = name
        self.width = width
        self.height = height
        self.cells: list[str] = []
        self.rects: dict[str, Rect] = {}
        self._id = 1

    def _next(self) -> str:
        self._id += 1
        return f"n{self._id}"

    def node(
        self, value: str, x: float, y: float, w: float, h: float, style: str, parent: str = "1"
    ) -> str:
        i = self._next()
        self.rects[i] = (x, y, w, h)
        self.cells.append(
            f'        <mxCell id="{i}" value={quoteattr(value)} style={quoteattr(style)} '
            f'vertex="1" parent="{parent}">\n'
            f'          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>\n'
            f"        </mxCell>"
        )
        return i

    def person(self, value: str, x: float, y: float, w: float, h: float) -> str:
        """A C4 person, drawn with the person icon rather than a plain box."""
        return self.node(value, x, y, w, h, S_PERSON_ICON)

    def vlink(
        self,
        a: str,
        b: str,
        value: str,
        style: str | None = None,
        lane: float | None = None,
        label_pos: float | None = None,
        jump: bool = False,
    ) -> str:
        """Join two nodes with one vertical segment at x `lane`, by default the
        centre of their horizontal overlap."""
        ax, ay, aw, ah = self.rects[a]
        bx, by, bw, bh = self.rects[b]
        lane = (max(ax, bx) + min(ax + aw, bx + bw)) / 2 if lane is None else lane
        a_below = ay > by
        ex, ey = (lane - ax) / aw, (0 if a_below else 1)
        nx, ny = (lane - bx) / bw, (1 if a_below else 0)
        mid = ((ay + ah + by) / 2) if not a_below else ((by + bh + ay) / 2)
        st = (style or S_EDGE) + anchor((round(ex, 4), ey), (round(nx, 4), ny))
        return self.edge(a, b, value, st, label_pos=label_pos, jump=jump, points=[(lane, mid)])

    def hlink(
        self,
        a: str,
        b: str,
        value: str,
        style: str | None = None,
        lane: float | None = None,
        label_pos: float | None = None,
        jump: bool = False,
    ) -> str:
        """Join two nodes with one horizontal segment at y `lane`, by default the
        centre of their vertical overlap."""
        ax, ay, aw, ah = self.rects[a]
        bx, by, bw, bh = self.rects[b]
        lane = (max(ay, by) + min(ay + ah, by + bh)) / 2 if lane is None else lane
        a_right = ax > bx
        ex, ey = (0 if a_right else 1), (lane - ay) / ah
        nx, ny = (1 if a_right else 0), (lane - by) / bh
        mid = ((bx + bw + ax) / 2) if a_right else ((ax + aw + bx) / 2)
        st = (style or S_EDGE) + anchor((ex, round(ey, 4)), (nx, round(ny, 4)))
        return self.edge(a, b, value, st, label_pos=label_pos, jump=jump, points=[(mid, lane)])

    def elbow(
        self,
        a: str,
        b: str,
        value: str,
        x: float,
        y: float,
        style: str | None = None,
        first: str = "v",
        label_pos: float | None = None,
        jump: bool = False,
    ) -> str:
        """Join two nodes with two segments through the corner (x, y).

        `first` is the leg that leaves `a`: "v" for vertical, "h" for horizontal.
        """
        ax, ay, aw, ah = self.rects[a]
        bx, by, bw, bh = self.rects[b]
        ex: float
        ey: float
        nx: float
        ny: float
        if first == "v":
            ex, ey = (x - ax) / aw, (0 if y < ay else 1)
            nx, ny = (0 if x < bx else 1), (y - by) / bh
        elif first == "h":
            ex, ey = (0 if x < ax else 1), (y - ay) / ah
            nx, ny = (x - bx) / bw, (0 if y < by else 1)
        else:
            raise ValueError(f"elbow: first must be 'v' or 'h', not {first!r}")
        st = (style or S_EDGE) + anchor((round(ex, 4), round(ey, 4)), (round(nx, 4), round(ny, 4)))
        return self.edge(a, b, value, st, label_pos=label_pos, jump=jump, points=[(x, y)])

    def route(
        self,
        a: str,
        b: str,
        value: str,
        corners: list[Point],
        style: str | None = None,
        label_pos: float | None = None,
        jump: bool = False,
    ) -> str:
        """Join two nodes through `corners`. Consecutive corners must share x or y.

        A corner within the node's width leaves or enters by its top or bottom.
        Any other corner uses its left or right side.
        """
        if not corners:
            raise ValueError("route: give at least one corner; use vlink/hlink for a lane")
        ax, ay, aw, ah = self.rects[a]
        bx, by, bw, bh = self.rects[b]
        fx, fy = corners[0]
        lx, ly = corners[-1]
        if ax <= fx <= ax + aw:  # leaves a by top or bottom
            exit_at: Point = ((fx - ax) / aw, 0 if fy < ay else 1)
        else:  # leaves a by left or right
            exit_at = (0 if fx < ax else 1, (fy - ay) / ah)
        if bx <= lx <= bx + bw:  # enters b by top or bottom
            entry_at: Point = ((lx - bx) / bw, 0 if ly < by else 1)
        else:
            entry_at = (0 if lx < bx else 1, (ly - by) / bh)
        st = (style or S_EDGE) + anchor(
            (round(exit_at[0], 4), round(exit_at[1], 4)),
            (round(entry_at[0], 4), round(entry_at[1], 4)),
        )
        return self.edge(a, b, value, st, label_pos=label_pos, jump=jump, points=list(corners))

    def edge(
        self,
        src: str,
        dst: str,
        value: str = "",
        style: str = S_EDGE,
        label_pos: float | None = None,
        points: list[Point] | None = None,
        jump: bool = False,
    ) -> str:
        """Add a raw edge.

        `label_pos` slides the label along the edge: -1 source, 0 middle, 1 target.
        `jump=True` adds a line jump, so emit this edge after the edge it crosses.
        """
        if jump:
            style += f"jumpStyle=arc;jumpSize={JUMP_SIZE};"
        i = self._next()
        inner = ""
        if points:
            pts = "\n".join(f'              <mxPoint x="{px}" y="{py}"/>' for px, py in points)
            inner += f'            <Array as="points">\n{pts}\n            </Array>\n'
        if label_pos is not None:
            inner += '            <mxPoint as="offset"/>\n'
        if inner:
            xattr = f'x="{label_pos}" ' if label_pos is not None else ""
            geom = (
                f'          <mxGeometry {xattr}relative="1" as="geometry">\n'
                f"{inner}"
                f"          </mxGeometry>"
            )
        else:
            geom = '          <mxGeometry relative="1" as="geometry"/>'
        self.cells.append(
            f'        <mxCell id="{i}" value={quoteattr(value)} style={quoteattr(style)} '
            f'edge="1" parent="1" source="{src}" target="{dst}">\n'
            f"{geom}\n"
            f"        </mxCell>"
        )
        return i

    def xml(self) -> str:
        body = "\n".join(self.cells)
        return (
            '<mxfile host="app.diagrams.net" type="device">\n'
            f'  <diagram name={quoteattr(self.name)} id="d1">\n'
            '    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" '
            'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            f'pageWidth="{self.width}" pageHeight="{self.height}" math="0" shadow="0">\n'
            "      <root>\n"
            '        <mxCell id="0"/>\n'
            '        <mxCell id="1" parent="0"/>\n'
            f"{body}\n"
            "      </root>\n"
            "    </mxGraphModel>\n"
            "  </diagram>\n"
            "</mxfile>\n"
        )

    def write(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.xml())
        print(f"wrote {path}")
