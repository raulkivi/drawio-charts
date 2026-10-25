#!/usr/bin/env python3
"""Rewrite compressed draw.io pages as plain, editable XML.

Usage: python3 decompress_drawio.py FILE [-o OUT | --in-place]

draw.io can save each <diagram> as base64(deflate(urlencode(xml))). That text
can't be edited by hand, so decode it first; draw.io opens the plain form
just as well. Files with no compressed pages are written back unchanged.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from drawio_io import decode_diagram


def decompress_string(text: str) -> str:
    root = ET.fromstring(text)
    changed = False
    for diagram in root.iter("diagram"):
        payload = (diagram.text or "").strip()
        if diagram.find("mxGraphModel") is not None or not payload:
            continue
        diagram.text = None
        diagram.append(ET.fromstring(decode_diagram(payload)))
        changed = True
    if not changed:
        return text
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode") + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("file")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("-o", "--output", help="write here instead of stdout")
    target.add_argument("--in-place", action="store_true", help="overwrite FILE")
    args = parser.parse_args(argv)

    result = decompress_string(Path(args.file).read_text(encoding="utf-8"))
    destination = args.file if args.in_place else args.output
    if destination:
        Path(destination).write_text(result, encoding="utf-8")
    else:
        sys.stdout.write(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
