"""Reading .drawio files: pages, compressed diagrams and cells.

Shared by validate_drawio.py and decompress_drawio.py. Standard library only.
"""

from __future__ import annotations

import base64
import urllib.parse
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass

# draw.io wraps cells that carry custom properties in one of these elements;
# the wrapper then holds the id and label, and the inner mxCell everything else.
WRAPPER_TAGS = ("UserObject", "object")


class DrawioFormatError(Exception):
    """The file is not a readable draw.io document."""


@dataclass
class Page:
    name: str | None
    id: str | None
    model: ET.Element | None
    error: str | None = None


@dataclass
class Cell:
    id: str | None
    element: ET.Element

    def get(self, attribute: str) -> str | None:
        return self.element.get(attribute)

    @property
    def is_vertex(self) -> bool:
        return self.get("vertex") == "1"

    @property
    def is_edge(self) -> bool:
        return self.get("edge") == "1"

    def geometry(self) -> ET.Element | None:
        return next((g for g in self.element.findall("mxGeometry") if g.get("as") == "geometry"), None)


def decode_diagram(text: str) -> str:
    """Inverse of draw.io's compression: base64 -> raw deflate -> URL-decode."""
    raw = base64.b64decode(text.strip(), validate=True)
    return urllib.parse.unquote(zlib.decompress(raw, -15).decode("utf-8"))


def parse_pages(text: str) -> list[Page]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        raise DrawioFormatError(f"XML is not well-formed: {error}") from None

    if root.tag == "mxGraphModel":
        return [Page(name=None, id=None, model=root)]
    diagrams = root.findall("diagram")
    if not diagrams:
        raise DrawioFormatError("no <diagram> or <mxGraphModel> element found")
    return [_read_page(diagram) for diagram in diagrams]


def _read_page(diagram: ET.Element) -> Page:
    page = Page(name=diagram.get("name"), id=diagram.get("id"), model=diagram.find("mxGraphModel"))
    if page.model is not None:
        return page
    payload = (diagram.text or "").strip()
    if not payload:
        page.error = "page has no <mxGraphModel>"
        return page
    try:
        page.model = ET.fromstring(decode_diagram(payload))
    except (ValueError, zlib.error, ET.ParseError) as error:
        page.error = f"could not decode compressed diagram: {error}"
    return page


def cells(model: ET.Element) -> list[Cell]:
    root = model.find("root")
    if root is None:
        return []
    found = []
    for child in root:
        if child.tag == "mxCell":
            found.append(Cell(id=child.get("id"), element=child))
        elif child.tag in WRAPPER_TAGS:
            inner = child.find("mxCell")
            if inner is not None:
                found.append(Cell(id=child.get("id"), element=inner))
    return found
