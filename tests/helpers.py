"""Shared test helpers: paths and tiny builders for .drawio XML."""

import base64
import sys
import urllib.parse
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "drawio-charts"
SCRIPTS_DIR = SKILL_DIR / "scripts"
EXAMPLES_DIR = SKILL_DIR / "assets" / "examples"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

ROOT_CELLS = '<mxCell id="0"/><mxCell id="1" parent="0"/>'


def graph_model(cells: str, root_cells: str = ROOT_CELLS) -> str:
    return f"<mxGraphModel><root>{root_cells}{cells}</root></mxGraphModel>"


def drawio(cells: str, name: str = "Page-1", root_cells: str = ROOT_CELLS) -> str:
    return (
        '<mxfile host="app.diagrams.net">'
        f'<diagram id="d1" name="{name}">{graph_model(cells, root_cells)}</diagram>'
        "</mxfile>"
    )


def compress(model_xml: str) -> str:
    """Encode a <mxGraphModel> the way draw.io does for compressed diagrams."""
    deflater = zlib.compressobj(9, zlib.DEFLATED, -15)
    raw = deflater.compress(urllib.parse.quote(model_xml, safe="").encode()) + deflater.flush()
    return base64.b64encode(raw).decode()


def vertex(cell_id: str, parent: str = "1", style: str = "rounded=1;", geometry: str | None = None) -> str:
    geometry = geometry or '<mxGeometry x="0" y="0" width="120" height="60" as="geometry"/>'
    return f'<mxCell id="{cell_id}" value="" style="{style}" parent="{parent}" vertex="1">{geometry}</mxCell>'


def edge(cell_id: str, source: str | None, target: str | None, parent: str = "1",
         style: str = "endArrow=classic;", geometry: str | None = None) -> str:
    geometry = geometry or '<mxGeometry relative="1" as="geometry"/>'
    terminals = "".join(
        f' {name}="{value}"' for name, value in (("source", source), ("target", target)) if value is not None
    )
    return f'<mxCell id="{cell_id}" style="{style}" parent="{parent}"{terminals} edge="1">{geometry}</mxCell>'
