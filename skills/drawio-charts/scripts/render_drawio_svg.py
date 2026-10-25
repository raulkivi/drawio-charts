#!/usr/bin/env python3
"""Render a .drawio file as an editable .drawio.svg, without the draw.io app.

Usage: python3 render_drawio_svg.py IN.drawio -o OUT.drawio.svg

The SVG shows the first page and carries the whole draw.io document in its
`content` attribute, so GitHub/GitLab display it as an image while draw.io
and the VS Code draw.io extension open it as an editable diagram (and
redraw the image on save). It draws the shapes, edges and markers this
skill's layout produces; anything else falls back to a labelled rectangle.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path

from drawio_io import Cell, cells, parse_pages
from edge_router import Rect, orthogonalise, side_anchor
from text_metrics import FONT_SIZE, label_lines, text_width, wrap

Point = tuple[float, float]
FONT = "Helvetica, Arial, sans-serif"
MARGIN = 10
SKIP_SHAPES = {"edgeLabel"}


Box = Rect


def parse_style(style: str | None) -> dict[str, str]:
    """`a=b;` pairs; bare words (named styles) map to themselves under "_names"."""
    result: dict[str, str] = {}
    names = []
    for part in (style or "").split(";"):
        if not part:
            continue
        if "=" in part:
            key, value = part.split("=", 1)
            result[key] = value
        else:
            names.append(part)
    result["_names"] = " ".join(names)
    return result


class Canvas:
    """SVG under construction, tracking the drawn extent for the viewBox."""

    def __init__(self) -> None:
        self.defs = ET.Element("defs")
        self.body = ET.Element("g")
        self.markers: set[str] = set()
        self.min_x = self.min_y = math.inf
        self.max_x = self.max_y = -math.inf

    def extend(self, *points: Point) -> None:
        for x, y in points:
            self.min_x, self.min_y = min(self.min_x, x), min(self.min_y, y)
            self.max_x, self.max_y = max(self.max_x, x), max(self.max_y, y)

    def add(self, tag: str, cell: str | None = None, **attributes: object) -> ET.Element:
        attrs = {k.replace("_", "-"): _fmt(v) for k, v in attributes.items() if v is not None}
        if cell is not None:
            attrs["data-cell"] = cell
        return ET.SubElement(self.body, tag, attrs)


def render_svg(xml_text: str) -> str:
    page = parse_pages(xml_text)[0]
    if page.model is None:
        raise ValueError(page.error or "page has no diagram")
    all_cells = cells(page.model)
    by_id = {c.id: c for c in all_cells}
    canvas = Canvas()
    renderer = _Renderer(canvas, by_id)
    renderer.assign_slots([c for c in all_cells if c.is_edge])
    for cell in all_cells:
        if cell.is_vertex and not _is_edge_child(cell, by_id):
            renderer.vertex(cell)
        elif cell.is_edge:
            renderer.edge(cell)
    for cell in all_cells:
        if cell.is_vertex and _is_edge_child(cell, by_id):
            renderer.edge_child_label(cell)

    if canvas.min_x is math.inf:
        canvas.extend((0, 0), (1, 1))
    width = math.ceil(canvas.max_x - canvas.min_x + 2 * MARGIN)
    height = math.ceil(canvas.max_y - canvas.min_y + 2 * MARGIN)
    svg = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg", "version": "1.1",
        "width": str(width), "height": str(height), "viewBox": f"0 0 {width} {height}",
        "style": "background-color: #ffffff;", "content": xml_text,
    })
    svg.append(canvas.defs)
    ET.SubElement(svg, "rect", {"x": "0", "y": "0", "width": str(width), "height": str(height), "fill": "#ffffff"})
    canvas.body.set("transform", f"translate({_fmt(MARGIN - canvas.min_x)},{_fmt(MARGIN - canvas.min_y)})")
    svg.append(canvas.body)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(svg, encoding="unicode") + "\n"


def path_points(d: str) -> list[Point]:
    numbers = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", d)]
    return list(zip(numbers[0::2], numbers[1::2]))


def _is_edge_child(cell: Cell, by_id: dict[str | None, Cell]) -> bool:
    parent = by_id.get(cell.get("parent"))
    return parent is not None and parent.is_edge


# --- vertices --------------------------------------------------------------

ShapeDrawer = Callable[["_Renderer", Cell, Box, dict], None]
SHAPES: dict[str, ShapeDrawer] = {}


def shape(*names: str):
    def register(fn: ShapeDrawer) -> ShapeDrawer:
        for name in names:
            SHAPES[name] = fn
        return fn
    return register


class _Renderer:
    def __init__(self, canvas: Canvas, by_id: dict[str | None, Cell]) -> None:
        self.c = canvas
        self.by_id = by_id
        self._origin_cache: dict[str, Point] = {}
        self.slots: dict[tuple[str, str], float] = {}   # (edge id, "start"/"end") -> 0..1 along the side

    def origin(self, cell_id: str | None) -> Point:
        """Absolute top-left of a cell's coordinate space (its parent chain)."""
        cell = self.by_id.get(cell_id)
        if cell is None or not cell.is_vertex:
            return (0.0, 0.0)
        if cell_id not in self._origin_cache:
            px, py = self.origin(cell.get("parent"))
            g = cell.geometry()
            self._origin_cache[cell_id] = (px + _float(g, "x"), py + _float(g, "y"))
        return self._origin_cache[cell_id]

    def box(self, cell: Cell) -> Box:
        x, y = self.origin(cell.id)
        g = cell.geometry()
        return Box(x, y, _float(g, "width"), _float(g, "height"))

    def vertex(self, cell: Cell) -> None:
        style = parse_style(cell.get("style"))
        name = style.get("shape") or next((n for n in style["_names"].split() if n in SHAPES or n in SKIP_SHAPES), "rect")
        if name in SKIP_SHAPES:
            return
        box = self.box(cell)
        self.c.extend((box.x, box.y), (box.x + box.w, box.y + box.h))
        SHAPES.get(name, SHAPES["rect"])(self, cell, box, style)

    # shared paint helpers
    def paint(self, style: dict, default_fill: str = "#ffffff") -> dict:
        fill = style.get("fillColor", default_fill)
        stroke = style.get("strokeColor", "#000000")
        return {
            "fill": "none" if fill in ("none", "") else fill,
            "stroke": "none" if stroke in ("none", "") else ("#666666" if stroke == "inherit" else stroke),
            "stroke_width": style.get("strokeWidth", "1"),
            "stroke_dasharray": "6 4" if style.get("dashed") == "1" else None,
        }

    def label(self, cell: Cell, style: dict, area: Box, value: str | None = None,
              default_align: str = "center", background: str | None = None) -> None:
        raw = cell.get("value") if value is None else value
        if not raw:
            return
        lines = label_lines(raw) if style.get("html") == "1" else raw.split("\n")
        size = float(style.get("fontSize", FONT_SIZE))
        align = style.get("align", default_align)
        spacing = float(style.get("spacingLeft", 4)) if align == "left" else 4
        if style.get("whiteSpace") == "wrap" and area.w > 20:
            lines = wrap(lines, area.w - 2 * spacing, size)
        line_height = size * 1.3
        valign = style.get("verticalAlign", "middle")
        total = line_height * len(lines)
        if valign == "top":
            first = area.y + 4 + size
        elif valign == "bottom":
            first = area.y + area.h - total - 2 + size
        else:
            first = area.cy - total / 2 + size * 0.95
        anchor = {"left": "start", "right": "end"}.get(align, "middle")
        x = {"left": area.x + spacing, "right": area.x + area.w - 4}.get(align, area.cx)
        font_style = int(style.get("fontStyle", "0") or 0)
        for i, line in enumerate(lines):
            y = first + i * line_height
            if background:
                w = text_width(line, size) + 6
                left = x - w / 2 if anchor == "middle" else (x - 3 if anchor == "start" else x - w + 3)
                self.c.add("rect", x=left, y=y - size, width=w, height=line_height, fill=background)
            text = self.c.add("text", cell.id, x=x, y=y, font_family=FONT, font_size=size, text_anchor=anchor,
                              fill=style.get("fontColor", "#000000"),
                              font_weight="bold" if font_style & 1 else None,
                              font_style="italic" if font_style & 2 else None,
                              text_decoration="underline" if font_style & 4 else None)
            text.text = line
            self.c.extend((x - text_width(line, size) / 2, y - size), (x + text_width(line, size) / 2, y + 4))

    # --- edges --------------------------------------------------------------

    def edge(self, cell: Cell) -> None:
        style = parse_style(cell.get("style"))
        points = self.route(cell, style)
        if len(points) < 2:
            return
        self.c.extend(*points)
        paint = self.paint(style, default_fill="none")
        stroke = paint["stroke"] if paint["stroke"] != "none" else None
        if stroke is None:
            return
        d = "M " + " L ".join(f"{_fmt(x)} {_fmt(y)}" for x, y in points)
        self.c.add("path", d=d, fill="none", stroke=stroke, stroke_width=paint["stroke_width"],
                   stroke_dasharray=paint["stroke_dasharray"],
                   marker_end=self.marker(style.get("endArrow", "classic"), style.get("endFill", "1"), stroke),
                   marker_start=self.marker(style.get("startArrow", "none"), style.get("startFill", "1"), stroke),
                   **{"data-edge": cell.id})
        if cell.get("value"):
            mid = _along(points, (_float(cell.geometry(), "x") + 1) / 2)
            if style.get("verticalAlign") == "bottom":
                if style.get("align") == "left":   # self-message: label right of the loop
                    area = Box(points[1][0] + 6, points[1][1] - 18, 200, 16)
                    self.label(cell, {**style, "whiteSpace": ""}, area, default_align="left")
                else:
                    area = Box(mid[0] - 150, mid[1] - 20, 300, 16)
                    self.label(cell, {**style, "whiteSpace": ""}, area)
            else:
                area = Box(mid[0] - 100, mid[1] - 10, 200, 20)
                self.label(cell, {**style, "whiteSpace": "", "verticalAlign": "middle"}, area, background="#ffffff")

    def edge_child_label(self, cell: Cell) -> None:
        edge = self.by_id[cell.get("parent")]
        points = self.route(edge, parse_style(edge.get("style")))
        if len(points) < 2:
            return
        fraction = (_float(cell.geometry(), "x") + 1) / 2
        x, y = _along(points, fraction)
        style = parse_style(cell.get("style"))
        self.label(cell, {**style, "whiteSpace": ""}, Box(x - 100, y - 10, 200, 20), background="#ffffff")

    def route(self, cell: Cell, style: dict) -> list[Point]:
        geometry = cell.geometry()
        ox, oy = self.origin(cell.get("parent"))
        waypoints, terminal = [], {}
        if geometry is not None:
            for point in geometry.findall("mxPoint"):
                terminal[point.get("as")] = (ox + _float(point, "x"), oy + _float(point, "y"))
            array = geometry.find("Array")
            if array is not None:
                waypoints = [(ox + _float(p, "x"), oy + _float(p, "y")) for p in array.findall("mxPoint")]
        source = self.by_id.get(cell.get("source"))
        target = self.by_id.get(cell.get("target"))
        source_box = self.box(source) if source is not None else None
        target_box = self.box(target) if target is not None else None

        def fixed(box: Box | None, prefix: str) -> Point | None:
            if box is None or f"{prefix}X" not in style:
                return None
            return (box.x + float(style[f"{prefix}X"]) * box.w + float(style.get(f"{prefix}Dx", 0)),
                    box.y + float(style.get(f"{prefix}Y", 0)) * box.h + float(style.get(f"{prefix}Dy", 0)))

        start = fixed(source_box, "exit") or terminal.get("sourcePoint")
        end = fixed(target_box, "entry") or terminal.get("targetPoint")
        orthogonal = style.get("edgeStyle") in ("orthogonalEdgeStyle", "elbowEdgeStyle", "entityRelationEdgeStyle")
        horizontal = style.get("edgeStyle") == "entityRelationEdgeStyle"
        sides = {}
        if start is None and source_box is not None:
            towards = waypoints[0] if waypoints else (end or (target_box and (target_box.cx, target_box.cy)))
            start, sides["start"] = side_anchor(source_box, towards, horizontal, self.slots.get((cell.id, "start"), 0.5))
        if end is None and target_box is not None:
            towards = waypoints[-1] if waypoints else start
            end, sides["end"] = side_anchor(target_box, towards, horizontal, self.slots.get((cell.id, "end"), 0.5))
        if start is None or end is None:
            return []
        points = [start, *waypoints, end]
        return orthogonalise(points, sides.get("start"), sides.get("end")) if orthogonal else points

    def assign_slots(self, edges: list[Cell]) -> None:
        """Spread edge ends that meet the same side of a node, ordered to avoid crossing."""
        by_side: dict[tuple[str, str], list[tuple[float, str, str]]] = {}
        for cell in edges:
            route = self.route(cell, parse_style(cell.get("style")))
            if len(route) < 2:
                continue
            style = parse_style(cell.get("style"))
            for end, cell_id, point, neighbour, constrained in (
                    ("start", cell.get("source"), route[0], route[1], "exitX" in style),
                    ("end", cell.get("target"), route[-1], route[-2], "entryX" in style)):
                box_cell = self.by_id.get(cell_id)
                if box_cell is None or constrained:
                    continue
                box = self.box(box_cell)
                side = _side_of(box, point)
                along = neighbour[0] if side in ("top", "bottom") else neighbour[1]
                by_side.setdefault((cell_id, side), []).append((along, cell.id, end))
        for ends in by_side.values():
            if len(ends) < 2:
                continue
            for i, (_, edge_id, end) in enumerate(sorted(ends)):
                self.slots[(edge_id, end)] = (i + 1) / (len(ends) + 1)

    def marker(self, kind: str, filled: str, colour: str) -> str | None:
        if kind in ("none", "") or kind not in MARKERS:
            return None
        marker_id = f"m-{kind}-{filled}-{colour.lstrip('#')}"
        if marker_id not in self.c.markers:
            self.c.markers.add(marker_id)
            marker = ET.SubElement(self.c.defs, "marker", {
                "id": marker_id, "viewBox": "0 0 12 12", "refX": MARKERS[kind][0], "refY": "6",
                "markerWidth": "12", "markerHeight": "12", "markerUnits": "userSpaceOnUse",
                "orient": "auto-start-reverse",
            })
            fill = colour if filled == "1" else "#ffffff"
            for tag, attributes in MARKERS[kind][1]:
                element_attrs = {k: v.replace("FILL", fill).replace("STROKE", colour) for k, v in attributes.items()}
                ET.SubElement(marker, tag, {"stroke": colour, **element_attrs})
        return f"url(#{marker_id})"


# Marker drawings in a 12x12 box pointing right, tip at refX.
MARKERS: dict[str, tuple[str, list[tuple[str, dict[str, str]]]]] = {
    "classic": ("12", [("path", {"d": "M0,1 L12,6 L0,11 z", "fill": "FILL"})]),
    "block": ("12", [("path", {"d": "M0,1 L12,6 L0,11 z", "fill": "FILL"})]),
    "open": ("12", [("path", {"d": "M1,1 L12,6 L1,11", "fill": "none"})]),
    "oval": ("12", [("circle", {"cx": "7", "cy": "6", "r": "4.5", "fill": "FILL"})]),
    "diamond": ("12", [("path", {"d": "M0,6 L6,1.5 L12,6 L6,10.5 z", "fill": "FILL"})]),
    "cross": ("6", [("path", {"d": "M2,2 L10,10 M10,2 L2,10", "fill": "none"})]),
    "ERmandOne": ("12", [("path", {"d": "M0,6 L12,6 M6,1 L6,11 M9,1 L9,11", "fill": "none"})]),
    "ERone": ("12", [("path", {"d": "M0,6 L12,6 M8,1 L8,11", "fill": "none"})]),
    "ERzeroToOne": ("12", [("path", {"d": "M7,6 L12,6 M9.5,1 L9.5,11", "fill": "none"}),
                           ("circle", {"cx": "4", "cy": "6", "r": "3", "fill": "#ffffff"})]),
    "ERoneToMany": ("12", [("path", {"d": "M0,6 L12,6 M6,6 L12,1 M6,6 L12,11 M4,1 L4,11", "fill": "none"})]),
    "ERmany": ("12", [("path", {"d": "M0,6 L12,6 M6,6 L12,1 M6,6 L12,11", "fill": "none"})]),
    "ERzeroToMany": ("12", [("path", {"d": "M7,6 L12,6 M7,6 L12,1 M7,6 L12,11", "fill": "none"}),
                            ("circle", {"cx": "3.5", "cy": "6", "r": "3", "fill": "#ffffff"})]),
}


def _side_of(box: Box, point: Point) -> str:
    distances = {"top": abs(point[1] - box.y), "bottom": abs(point[1] - box.y - box.h),
                 "left": abs(point[0] - box.x), "right": abs(point[0] - box.x - box.w)}
    return min(distances, key=distances.get)


def _along(points: list[Point], fraction: float) -> Point:
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:])]
    target = sum(lengths) * min(max(fraction, 0), 1)
    for (a, b), length in zip(zip(points, points[1:]), lengths):
        if target <= length and length:
            t = target / length
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        target -= length
    return points[-1]


# --- shape drawers -----------------------------------------------------------

@shape("rect", "label")
def _rect(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    rx = 0.0
    if style.get("rounded") == "1":
        rx = box.h / 2 if style.get("arcSize") == "50" else min(box.w, box.h) * float(style.get("arcSize", 15)) / 200
    r.c.add("rect", cell.id, x=box.x, y=box.y, width=box.w, height=box.h, rx=rx or None, **r.paint(style))
    r.label(cell, style, box)


@shape("text")
def _text(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    r.c.add("rect", cell.id, x=box.x, y=box.y, width=box.w, height=box.h, fill="none", stroke="none")
    r.label(cell, style, box)


@shape("ellipse")
def _ellipse(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    r.c.add("ellipse", cell.id, cx=box.cx, cy=box.cy, rx=box.w / 2, ry=box.h / 2, **r.paint(style))
    r.label(cell, style, box)


@shape("doubleEllipse")
def _double_ellipse(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    paint = r.paint(style)
    r.c.add("ellipse", cell.id, cx=box.cx, cy=box.cy, rx=box.w / 2, ry=box.h / 2, **paint)
    r.c.add("ellipse", cx=box.cx, cy=box.cy, rx=box.w / 2 - 4, ry=box.h / 2 - 4, **{**paint, "fill": "none"})
    r.label(cell, style, box)


@shape("endState")
def _end_state(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    paint = r.paint(style)
    r.c.add("ellipse", cell.id, cx=box.cx, cy=box.cy, rx=box.w / 2, ry=box.h / 2, **{**paint, "fill": "#ffffff"})
    r.c.add("ellipse", cx=box.cx, cy=box.cy, rx=box.w / 2 - 5, ry=box.h / 2 - 5, **paint)


def _polygon(r: _Renderer, cell: Cell, box: Box, style: dict, points: list[Point]) -> None:
    r.c.add("polygon", cell.id, points=" ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in points), **r.paint(style))
    r.label(cell, style, box)


@shape("rhombus")
def _rhombus(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    _polygon(r, cell, box, style, [(box.cx, box.y), (box.x + box.w, box.cy), (box.cx, box.y + box.h), (box.x, box.cy)])


@shape("hexagon")
def _hexagon(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    s = float(style.get("size", 15))
    _polygon(r, cell, box, style, [(box.x + s, box.y), (box.x + box.w - s, box.y), (box.x + box.w, box.cy),
                                   (box.x + box.w - s, box.y + box.h), (box.x + s, box.y + box.h), (box.x, box.cy)])


@shape("parallelogram")
def _parallelogram(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    s = float(style.get("size", 15))
    _polygon(r, cell, box, style, [(box.x + s, box.y), (box.x + box.w, box.y),
                                   (box.x + box.w - s, box.y + box.h), (box.x, box.y + box.h)])


@shape("trapezoid")
def _trapezoid(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    s = float(style.get("size", 15))
    _polygon(r, cell, box, style, [(box.x + s, box.y), (box.x + box.w - s, box.y),
                                   (box.x + box.w, box.y + box.h), (box.x, box.y + box.h)])


@shape("step")
def _step(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    s = float(style.get("size", 15))
    _polygon(r, cell, box, style, [(box.x, box.y), (box.x + box.w - s, box.y), (box.x + box.w, box.cy),
                                   (box.x + box.w - s, box.y + box.h), (box.x, box.y + box.h), (box.x + s, box.cy)])


@shape("process")
def _process(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    paint = r.paint(style)
    r.c.add("rect", cell.id, x=box.x, y=box.y, width=box.w, height=box.h, **paint)
    inset = box.w * 0.1
    for x in (box.x + inset, box.x + box.w - inset):
        r.c.add("line", x1=x, y1=box.y, x2=x, y2=box.y + box.h, stroke=paint["stroke"])
    r.label(cell, style, box)


@shape("cylinder", "cylinder3")
def _cylinder(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    s = min(float(style.get("size", 10)), box.h / 3)
    rx = box.w / 2
    body = (f"M {_fmt(box.x)} {_fmt(box.y + s)} A {_fmt(rx)} {_fmt(s)} 0 0 1 {_fmt(box.x + box.w)} {_fmt(box.y + s)} "
            f"L {_fmt(box.x + box.w)} {_fmt(box.y + box.h - s)} A {_fmt(rx)} {_fmt(s)} 0 0 1 {_fmt(box.x)} "
            f"{_fmt(box.y + box.h - s)} Z")
    paint = r.paint(style)
    r.c.add("path", cell.id, d=body, **paint)
    r.c.add("path", d=f"M {_fmt(box.x)} {_fmt(box.y + s)} A {_fmt(rx)} {_fmt(s)} 0 0 0 {_fmt(box.x + box.w)} "
                      f"{_fmt(box.y + s)}", fill="none", stroke=paint["stroke"])
    r.label(cell, style, Box(box.x, box.y + s, box.w, box.h - s))


@shape("note")
def _note(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    s = float(style.get("size", 12))
    paint = r.paint(style)
    r.c.add("path", cell.id, d=(f"M {_fmt(box.x)} {_fmt(box.y)} L {_fmt(box.x + box.w - s)} {_fmt(box.y)} "
                                f"L {_fmt(box.x + box.w)} {_fmt(box.y + s)} L {_fmt(box.x + box.w)} {_fmt(box.y + box.h)} "
                                f"L {_fmt(box.x)} {_fmt(box.y + box.h)} Z"), **paint)
    r.c.add("path", d=(f"M {_fmt(box.x + box.w - s)} {_fmt(box.y)} L {_fmt(box.x + box.w - s)} {_fmt(box.y + s)} "
                       f"L {_fmt(box.x + box.w)} {_fmt(box.y + s)}"), fill="none", stroke=paint["stroke"])
    r.label(cell, style, box)


@shape("swimlane")
def _swimlane(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    header = float(style.get("startSize", 26))
    paint = r.paint(style)
    rx = 6 if style.get("rounded") == "1" else None
    r.c.add("rect", cell.id, x=box.x, y=box.y, width=box.w, height=box.h, rx=rx,
            **{**paint, "fill": style.get("swimlaneFillColor", "#ffffff")})
    r.c.add("rect", x=box.x, y=box.y, width=box.w, height=header, rx=rx, **paint)
    r.label(cell, {**style, "verticalAlign": "middle"}, Box(box.x, box.y, box.w, header))


@shape("line")
def _divider(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    r.c.add("line", cell.id, x1=box.x, y1=box.cy, x2=box.x + box.w, y2=box.cy, stroke=r.paint(style)["stroke"])


@shape("umlLifeline")
def _lifeline(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    size = float(style.get("size", 40))
    paint = r.paint(style)
    line_top = box.y + size
    if style.get("participant") == "umlActor":
        _stick_figure(r, cell, Box(box.cx - 12, box.y, 24, size), paint["stroke"])
        r.label(cell, {**style, "whiteSpace": ""}, Box(box.x, box.y + size, box.w, 18), background="#ffffff")
        line_top += 20
    else:
        r.c.add("rect", cell.id, x=box.x, y=box.y, width=box.w, height=size, **paint)
        r.label(cell, style, Box(box.x, box.y, box.w, size))
    r.c.add("line", x1=box.cx, y1=line_top, x2=box.cx, y2=box.y + box.h, stroke=paint["stroke"], stroke_dasharray="6 4")


def _stick_figure(r: _Renderer, cell: Cell, box: Box, stroke: str) -> None:
    head = box.h * 0.18
    r.c.add("circle", cell.id, cx=box.cx, cy=box.y + head, r=head, fill="#ffffff", stroke=stroke)
    neck, hips = box.y + 2 * head, box.y + box.h * 0.65
    r.c.add("path", d=(f"M {_fmt(box.cx)} {_fmt(neck)} L {_fmt(box.cx)} {_fmt(hips)} "
                       f"M {_fmt(box.x)} {_fmt(neck + head)} L {_fmt(box.x + box.w)} {_fmt(neck + head)} "
                       f"M {_fmt(box.x + 2)} {_fmt(box.y + box.h)} L {_fmt(box.cx)} {_fmt(hips)} "
                       f"L {_fmt(box.x + box.w - 2)} {_fmt(box.y + box.h)}"), fill="none", stroke=stroke)


@shape("umlActivation")
def _activation(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    r.c.add("rect", cell.id, x=box.x, y=box.y, width=box.w, height=box.h, **r.paint(style))


@shape("umlFrame")
def _frame(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    tab_w, tab_h = float(style.get("width", 60)), float(style.get("height", 26))
    paint = r.paint(style, default_fill="none")
    r.c.add("rect", cell.id, x=box.x, y=box.y, width=box.w, height=box.h, **paint)
    r.c.add("path", d=(f"M {_fmt(box.x)} {_fmt(box.y)} L {_fmt(box.x + tab_w)} {_fmt(box.y)} "
                       f"L {_fmt(box.x + tab_w)} {_fmt(box.y + tab_h - 8)} L {_fmt(box.x + tab_w - 8)} "
                       f"{_fmt(box.y + tab_h)} L {_fmt(box.x)} {_fmt(box.y + tab_h)} Z"),
            fill="#f5f5f5", stroke=paint["stroke"])
    r.label(cell, {**style, "fontStyle": "1"}, Box(box.x, box.y, tab_w - 4, tab_h))


@shape("image")
def _image(r: _Renderer, cell: Cell, box: Box, style: dict) -> None:
    r.c.add("rect", cell.id, x=box.x, y=box.y, width=box.w, height=box.h, fill="#f5f5f5", stroke="#999999",
            stroke_dasharray="4 3")
    r.label(cell, {**style, "whiteSpace": "", "verticalAlign": "top"}, Box(box.x - 40, box.y + box.h, box.w + 80, 20))


# --- plumbing ------------------------------------------------------------------

def _float(element: ET.Element | None, name: str) -> float:
    if element is None:
        return 0.0
    try:
        return float(element.get(name, 0))
    except ValueError:
        return 0.0


def _fmt(value: object) -> str:
    if isinstance(value, float):
        rounded = round(value, 2)
        return str(int(rounded)) if rounded == int(rounded) else str(rounded)
    return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("file", help=".drawio file to render")
    parser.add_argument("-o", "--output", required=True, help="output .drawio.svg path")
    args = parser.parse_args(argv)
    Path(args.output).write_text(render_svg(Path(args.file).read_text(encoding="utf-8")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
