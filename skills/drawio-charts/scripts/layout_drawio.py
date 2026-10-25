#!/usr/bin/env python3
"""Lay out a graph spec (JSON) and write it as a .drawio file.

Usage: python3 layout_drawio.py SPEC.json -o OUT.drawio
       python3 layout_drawio.py SPEC.json -o OUT.drawio.svg   (editable SVG for docs)
       (SPEC may be "-" to read the spec from stdin)

The spec format is in references/mermaid-mapping.md. Exits 2 when the spec
is invalid, with the reason on stderr.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from graph_render import render_graph
from graph_spec import GRAPH_TYPES, Spec, SpecError, parse_spec
from render_drawio_svg import render_svg
from sequence_render import render_sequence

RENDERERS: dict[str, Callable[[Spec], str]] = {
    **dict.fromkeys(GRAPH_TYPES, render_graph),
    "sequence": render_sequence,
}

__all__ = ["convert", "main", "parse_spec"]


def convert(spec: Spec) -> str:
    return RENDERERS[spec.type](spec)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("spec", help='spec JSON file, or "-" for stdin')
    parser.add_argument("-o", "--output", required=True, help="output path: .drawio, or .drawio.svg to render")
    args = parser.parse_args(argv)
    try:
        text = sys.stdin.read() if args.spec == "-" else Path(args.spec).read_text(encoding="utf-8")
        spec = parse_spec(json.loads(text))
    except (OSError, json.JSONDecodeError, SpecError) as error:
        print(f"spec error: {error}", file=sys.stderr)
        return 2
    xml = convert(spec)
    output = render_svg(xml) if args.output.endswith(".svg") else xml
    Path(args.output).write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
