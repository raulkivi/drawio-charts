"""Builds .drawio XML from cells. Knows the file format, not diagram types."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET

Point = tuple[float, float]


def html_label(text: str) -> str:
    """Escape text for a cell with html=1; newlines become <br>."""
    return "<br>".join(html.escape(line, quote=False) for line in text.split("\n"))


def style_string(**properties: object) -> str:
    return "".join(f"{key}={value};" for key, value in properties.items() if value is not None)


class DrawioBuilder:
    """Collects cells and writes one page. Ids are kept unique and clear of "0"/"1"."""

    def __init__(self) -> None:
        self._cells: list[ET.Element] = []
        self._ids: set[str] = {"0", "1"}

    def new_id(self, wanted: str) -> str:
        base = re.sub(r"\s+", "-", str(wanted)) or "cell"
        candidate, n = base, 2
        while candidate in self._ids:
            candidate = f"{base}-{n}"
            n += 1
        self._ids.add(candidate)
        return candidate

    def vertex(self, cell_id: str, value: str, style: str, parent: str,
               x: float, y: float, width: float, height: float, **attributes: str) -> str:
        cell = ET.Element("mxCell", {"id": cell_id, "value": value, "style": style, "parent": parent,
                                     "vertex": "1", **attributes})
        ET.SubElement(cell, "mxGeometry", {"x": _num(x), "y": _num(y), "width": _num(width),
                                           "height": _num(height), "as": "geometry"})
        self._cells.append(cell)
        return cell_id

    def edge(self, cell_id: str, value: str, style: str, parent: str,
             source: str | None = None, target: str | None = None,
             points: list[Point] = (), source_point: Point | None = None,
             target_point: Point | None = None) -> str:
        attributes = {"id": cell_id, "value": value, "style": style, "parent": parent}
        if source is not None:
            attributes["source"] = source
        if target is not None:
            attributes["target"] = target
        attributes["edge"] = "1"
        cell = ET.Element("mxCell", attributes)
        geometry = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
        for point, name in ((source_point, "sourcePoint"), (target_point, "targetPoint")):
            if point is not None:
                ET.SubElement(geometry, "mxPoint", {"x": _num(point[0]), "y": _num(point[1]), "as": name})
        if points:
            array = ET.SubElement(geometry, "Array", {"as": "points"})
            for x, y in points:
                ET.SubElement(array, "mxPoint", {"x": _num(x), "y": _num(y)})
        self._cells.append(cell)
        return cell_id

    def edge_label(self, cell_id: str, value: str, edge_id: str, position: float) -> str:
        """A label cell riding on an edge; position runs -1 (source) .. 1 (target)."""
        cell = ET.Element("mxCell", {"id": cell_id, "value": value, "parent": edge_id, "vertex": "1",
                                     "connectable": "0",
                                     "style": "edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];"})
        geometry = ET.SubElement(cell, "mxGeometry", {"x": _num(position), "relative": "1", "as": "geometry"})
        ET.SubElement(geometry, "mxPoint", {"as": "offset"})
        self._cells.append(cell)
        return cell_id

    def to_xml(self, name: str, width: float, height: float) -> str:
        mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "agent": "drawio-charts", "version": "21.0.0"})
        page_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "page-1"
        diagram = ET.SubElement(mxfile, "diagram", {"id": page_id, "name": name})
        model = ET.SubElement(diagram, "mxGraphModel", {
            "dx": "1200", "dy": "800", "grid": "1", "gridSize": "10", "guides": "1", "tooltips": "1",
            "connect": "1", "arrows": "1", "fold": "1", "page": "1", "pageScale": "1",
            "pageWidth": _num(max(1100, width)), "pageHeight": _num(max(850, height)),
        })
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", {"id": "0"})
        ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
        root.extend(self._cells)
        ET.indent(mxfile, space="  ")
        return ET.tostring(mxfile, encoding="unicode") + "\n"


def _num(value: float) -> str:
    rounded = round(float(value), 2)
    return str(int(rounded)) if rounded == int(rounded) else str(rounded)
