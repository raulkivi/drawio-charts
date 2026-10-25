#!/usr/bin/env python3
"""Validate .drawio files for the structural mistakes that break diagrams.

Usage: python3 validate_drawio.py FILE [FILE ...]

Prints "<file>: OK" or one line per issue; exits 1 if any file has issues.
Each rule is a small check function registered in CHECKS, so adding a rule
means adding a function, not editing the others.
"""

from __future__ import annotations

import sys
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from drawio_io import Cell, DrawioFormatError, Page, cells, parse_pages

ROOT_ID = "0"


@dataclass
class Issue:
    message: str
    diagram: str | None = None
    cell_id: str | None = None

    def __str__(self) -> str:
        where = []
        if self.diagram is not None:
            where.append(f"page '{self.diagram}'")
        if self.cell_id is not None:
            where.append(f"cell '{self.cell_id}'")
        return f"[{', '.join(where)}] {self.message}" if where else self.message


@dataclass
class PageContext:
    """One page's cells, indexed once and shared by every check."""

    cells: list[Cell]

    def __post_init__(self) -> None:
        self.by_id = {cell.id: cell for cell in self.cells if cell.id is not None}
        self.layer_ids = {cell.id for cell in self.cells if cell.get("parent") == ROOT_ID}

    def content_cells(self) -> Iterable[Cell]:
        """Cells below a layer: shapes, connectors, labels."""
        return (c for c in self.cells if c.get("parent") is not None and c.id not in self.layer_ids)

    def single_kind(self, edges: bool) -> Iterable[Cell]:
        for cell in self.content_cells():
            if cell.is_vertex != cell.is_edge and cell.is_edge == edges:
                yield cell


Check = Callable[[PageContext], Iterable[Issue]]


def check_unique_ids(page: PageContext) -> Iterable[Issue]:
    counts = Counter(cell.id for cell in page.cells)
    for cell_id, count in counts.items():
        if cell_id is None:
            yield Issue("cell has no id")
        elif count > 1:
            yield Issue(f"duplicate id (used {count} times)", cell_id=cell_id)


def check_root_and_layer(page: PageContext) -> Iterable[Issue]:
    if ROOT_ID not in page.by_id:
        yield Issue(f'missing root cell "{ROOT_ID}" (<mxCell id="{ROOT_ID}"/>)')
    elif not page.layer_ids:
        yield Issue(f'no layer: add <mxCell id="1" parent="{ROOT_ID}"/>')


def check_parents(page: PageContext) -> Iterable[Issue]:
    for cell in page.cells:
        parent = cell.get("parent")
        if parent is None:
            continue
        if parent == cell.id:
            yield Issue("cell is its own parent", cell_id=cell.id)
        elif parent not in page.by_id:
            yield Issue(f'parent "{parent}" does not exist', cell_id=cell.id)


def check_kind(page: PageContext) -> Iterable[Issue]:
    for cell in page.content_cells():
        if cell.is_vertex and cell.is_edge:
            yield Issue('cell is marked as both vertex="1" and edge="1"', cell_id=cell.id)
        elif not (cell.is_vertex or cell.is_edge):
            yield Issue('cell needs vertex="1" or edge="1"', cell_id=cell.id)


def check_edge_terminals(page: PageContext) -> Iterable[Issue]:
    for cell in page.single_kind(edges=True):
        geometry = cell.geometry()
        points = set() if geometry is None else {p.get("as") for p in geometry.findall("mxPoint")}
        for end in ("source", "target"):
            terminal = cell.get(end)
            if terminal is None:
                if f"{end}Point" not in points:
                    yield Issue(f"edge has no {end} and no {end}Point", cell_id=cell.id)
            elif terminal not in page.by_id:
                yield Issue(f'{end} "{terminal}" does not exist', cell_id=cell.id)
            elif terminal == ROOT_ID or terminal in page.layer_ids:
                yield Issue(f'{end} "{terminal}" is the root or a layer, not a shape', cell_id=cell.id)


def check_vertex_geometry(page: PageContext) -> Iterable[Issue]:
    for cell in page.single_kind(edges=False):
        geometry = cell.geometry()
        if geometry is None:
            yield Issue('vertex is missing <mxGeometry as="geometry">', cell_id=cell.id)
            continue
        if geometry.get("relative") == "1":
            continue  # edge labels and relative children are sized by their parent
        for dimension in ("width", "height"):
            if not _is_number(geometry.get(dimension)):
                yield Issue(f"vertex geometry needs a numeric {dimension}", cell_id=cell.id)


def check_edge_geometry(page: PageContext) -> Iterable[Issue]:
    for cell in page.single_kind(edges=True):
        if cell.geometry() is None:
            yield Issue('edge is missing <mxGeometry relative="1" as="geometry">', cell_id=cell.id)


def check_style_separators(page: PageContext) -> Iterable[Issue]:
    for cell in page.cells:
        for entry in (cell.get("style") or "").split(";"):
            key, _, value = entry.partition("=")
            if key.strip() != "image" and "=" in value:  # image data URIs legitimately contain '='
                yield Issue(f"style entry '{entry}' looks like a missing ';'", cell_id=cell.id)


CHECKS: list[Check] = [
    check_unique_ids,
    check_root_and_layer,
    check_parents,
    check_kind,
    check_edge_terminals,
    check_vertex_geometry,
    check_edge_geometry,
    check_style_separators,
]


def _is_number(value: str | None) -> bool:
    try:
        float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return True


def validate_page(page: Page, checks: list[Check] = CHECKS) -> list[Issue]:
    if page.error:
        return [Issue(page.error, diagram=page.name)]
    context = PageContext(cells(page.model))
    issues = [issue for check in checks for issue in check(context)]
    for issue in issues:
        issue.diagram = page.name
    return issues


def validate_string(text: str, checks: list[Check] = CHECKS) -> list[Issue]:
    try:
        pages = parse_pages(text)
    except DrawioFormatError as error:
        return [Issue(str(error))]
    issues = [Issue(f'duplicate diagram id "{page_id}"') for page_id, count in
              Counter(p.id for p in pages if p.id is not None).items() if count > 1]
    return issues + [issue for page in pages for issue in validate_page(page, checks)]


def validate_file(path: str | Path, checks: list[Check] = CHECKS) -> list[Issue]:
    return validate_string(Path(path).read_text(encoding="utf-8"), checks)


def main(argv: list[str] | None = None) -> int:
    paths = sys.argv[1:] if argv is None else argv
    if not paths:
        print(__doc__.strip().splitlines()[2])
        return 2
    failed = False
    for path in paths:
        try:
            issues = validate_file(path)
        except (OSError, UnicodeDecodeError) as error:
            print(f"{path}: cannot read ({error})")
            failed = True
            continue
        if issues:
            failed = True
            for issue in issues:
                print(f"{path}: {issue}")
        else:
            print(f"{path}: OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
