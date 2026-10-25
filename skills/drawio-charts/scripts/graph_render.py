"""Flowchart, state, class and ER specs -> draw.io cells.

Groups (Mermaid subgraphs, composite states) are laid out bottom-up: each
group's content is laid out first, then the group is placed as one box in
its parent's layout. Each edge is laid out at the deepest group holding
both ends, and its waypoints are relative to that group, as draw.io expects.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from drawio_writer import DrawioBuilder, html_label, style_string
from edge_router import Rect, default_route, route_around, route_crosses
from graph_spec import Edge, GraphSpec, Group, Node
from layered_layout import layered_layout
from text_metrics import fit_box, round_up, text_width

ROOT = None
MARGIN = 40
GROUP_PAD = 20
GROUP_HEADER = 30
ROW_HEIGHT = 26
CLASS_ROW_HEIGHT = 22
DIVIDER_HEIGHT = 8

PRIMARY = {"fillColor": "#dae8fc", "strokeColor": "#6c8ebf"}
DECISION = {"fillColor": "#fff2cc", "strokeColor": "#d6b656"}
BLACK = {"fillColor": "#000000", "strokeColor": "#000000"}

SHAPE_STYLES: dict[str, str] = {
    "rect": "rounded=0;whiteSpace=wrap;html=1;",
    "rounded": "rounded=1;whiteSpace=wrap;html=1;",
    "stadium": "rounded=1;arcSize=50;whiteSpace=wrap;html=1;",
    "subroutine": "shape=process;whiteSpace=wrap;html=1;backgroundOutline=1;",
    "cylinder": "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;",
    "circle": "ellipse;whiteSpace=wrap;html=1;aspect=fixed;",
    "doublecircle": "ellipse;shape=doubleEllipse;whiteSpace=wrap;html=1;aspect=fixed;",
    "rhombus": "rhombus;whiteSpace=wrap;html=1;",
    "hexagon": "shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fixedSize=1;size=15;",
    "parallelogram": "shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;fixedSize=1;size=15;",
    "trapezoid": "shape=trapezoid;perimeter=trapezoidPerimeter;whiteSpace=wrap;html=1;fixedSize=1;size=15;",
    "asymmetric": "shape=step;perimeter=stepPerimeter;whiteSpace=wrap;html=1;fixedSize=1;size=15;",
    "text": "text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;",
    "note": "shape=note;whiteSpace=wrap;html=1;size=14;backgroundOutline=1;",
    "start": "ellipse;html=1;aspect=fixed;",
    "end": "ellipse;shape=endState;html=1;aspect=fixed;",
    "fork": "rounded=0;html=1;",
}
SHAPE_COLOURS = {"rhombus": DECISION, "note": DECISION, "start": BLACK, "end": BLACK, "fork": BLACK, "text": {}}

CONTAINER_STYLE = ("swimlane;startSize=26;container=1;collapsible=0;html=1;fontStyle=1;"
                   "fillColor=#f5f5f5;strokeColor=#666666;swimlaneFillColor=#fafafa;")
TABLE_STYLE = ("swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;startSize={header};horizontalStack=0;"
               "resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=0;marginBottom=0;html=1;"
               "fillColor=#dae8fc;strokeColor=#6c8ebf;")
ROW_STYLE = ("text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=6;spacingRight=4;"
             "overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;whiteSpace=wrap;html=1;")
DIVIDER_STYLE = ("line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;spacingLeft=3;"
                 "spacingRight=3;rotatable=0;labelPosition=right;points=[];portConstraint=eastwest;strokeColor=inherit;")

MARKERS = {  # spec marker -> (draw.io arrow, filled)
    "none": ("none", 0), "arrow": ("classic", 1), "open": ("open", 0), "triangle": ("block", 0),
    "diamond": ("diamond", 1), "odiamond": ("diamond", 0), "circle": ("oval", 0), "cross": ("cross", 0),
    "one": ("ERmandOne", 0), "zero_or_one": ("ERzeroToOne", 0),
    "one_or_more": ("ERoneToMany", 0), "zero_or_more": ("ERzeroToMany", 0),
}
CSS_TO_STYLE = {"fill": "fillColor", "stroke": "strokeColor", "color": "fontColor", "stroke-width": "strokeWidth"}


@dataclass
class Box:
    width: float
    height: float


@dataclass
class Placed:
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0
    parent: str | None = ROOT


@dataclass
class Plan:
    """Where everything goes; positions are relative to each item's parent."""
    nodes: dict[str, Placed] = field(default_factory=dict)
    groups: dict[str, Placed] = field(default_factory=dict)
    edge_parent: dict[int, str | None] = field(default_factory=dict)
    edge_points: dict[int, list[tuple[float, float]]] = field(default_factory=dict)
    width: float = 0
    height: float = 0


def render_graph(spec: GraphSpec) -> str:
    plan = plan_layout(spec)
    extras = refine_edges(spec, plan)
    builder = DrawioBuilder()
    cell_id: dict[str, str] = {}
    groups = {g.id: g for g in _walk(spec.groups)}

    def parent_cell(owner: str | None) -> str:
        return "1" if owner is ROOT else cell_id[owner]

    for group_id in _top_down(spec.groups):  # containers before their children
        placed = plan.groups[group_id]
        cell_id[group_id] = builder.new_id(group_id)
        style = CONTAINER_STYLE + ("rounded=1;arcSize=6;" if spec.type == "state" else "")
        builder.vertex(cell_id[group_id], html_label(groups[group_id].label), style,
                       parent_cell(placed.parent), placed.x, placed.y, placed.width, placed.height)
    for node in spec.nodes:
        cell_id[node.id] = builder.new_id(node.id)
        _emit_node(builder, node, cell_id[node.id], plan.nodes[node.id], parent_cell(plan.nodes[node.id].parent), spec)
    for index, edge in enumerate(spec.edges):
        style, label_position = extras[index]
        _emit_edge(builder, index, edge, cell_id, parent_cell(plan.edge_parent[index]), plan.edge_points[index],
                   style, label_position)
    return builder.to_xml(spec.title or "Page-1", plan.width, plan.height)


def plan_layout(spec: GraphSpec) -> Plan:
    plan = Plan()
    owner: dict[str, str | None] = {n.id: ROOT for n in spec.nodes}
    group_parent: dict[str, str | None] = {}
    for group, parent in _walk_with_parent(spec.groups, ROOT):
        group_parent[group.id] = parent
        for member in group.members:
            owner[member] = group.id

    def containers(element: str) -> list[str | None]:
        """Groups holding the element, innermost first, ending with ROOT."""
        chain, current = [], (owner[element] if element in owner else group_parent[element])
        while current is not ROOT:
            chain.append(current)
            current = group_parent[current]
        return chain + [ROOT]

    def child_towards(level: str | None, element: str) -> str:
        if (owner.get(element, group_parent.get(element))) == level:
            return element
        return next(c for c in containers(element) if c is not ROOT and group_parent[c] == level)

    level_edges: dict[str | None, list[tuple[int, str, str]]] = {}
    for index, edge in enumerate(spec.edges):
        source_chain = containers(edge.source)
        level = next(c for c in containers(edge.target) if c in source_chain)
        plan.edge_parent[index] = level
        plan.edge_points[index] = []
        u, v = child_towards(level, edge.source), child_towards(level, edge.target)
        if u != v:
            level_edges.setdefault(level, []).append((index, u, v))

    nodes = {n.id: n for n in spec.nodes}
    groups = {g.id: g for g in _walk(spec.groups)}
    # side-by-side ranks need room for edge labels between them
    widest_label = max((text_width(e.label) for e in spec.edges if e.label), default=0)
    rank_gap = max(60, round_up(widest_label + 50)) if spec.direction in ("LR", "RL") else 60

    def lay_out(level: str | None) -> Box:
        members = [n.id for n in spec.nodes if owner[n.id] == level]
        subgroups = [g for g in groups if group_parent[g] == level]
        sizes: dict[str, Box] = {m: measure(nodes[m], spec.direction) for m in members}
        for group_id in subgroups:
            content = lay_out(group_id)
            label_width = text_width(groups[group_id].label) + 40
            sizes[group_id] = Box(max(content.width + 2 * GROUP_PAD, label_width),
                                  content.height + 2 * GROUP_PAD + GROUP_HEADER)
        children = members + subgroups
        result = layered_layout([(c, sizes[c].width, sizes[c].height) for c in children],
                                level_edges.get(level, []), spec.direction, rank_gap=rank_gap)
        if level is ROOT:
            dx, dy = MARGIN, MARGIN
        else:
            dx, dy = GROUP_PAD, GROUP_HEADER + GROUP_PAD
        for child in children:
            x, y = result.positions[child]
            placed = Placed(round(x + dx), round(y + dy), sizes[child].width, sizes[child].height, level)
            (plan.groups if child in groups else plan.nodes)[child] = placed
        for index, _, _ in level_edges.get(level, []):
            plan.edge_points[index] = [(round(x + dx), round(y + dy)) for x, y in result.edge_points[index]]
        return Box(result.size[0], result.size[1])

    total = lay_out(ROOT)
    plan.width, plan.height = total.width + 2 * MARGIN, total.height + 2 * MARGIN
    return plan


def refine_edges(spec: GraphSpec, plan: Plan) -> dict[int, tuple[dict[str, object], float | None]]:
    """Second pass over the edges once every box is placed.

    Edges between the same two nodes get their own exit/entry points and
    staggered labels, so they don't draw on top of each other. An edge whose
    simple route would run through another node gets detour waypoints.
    Returns extra style properties and a label position per edge index.
    """
    extras: dict[int, tuple[dict[str, object], float | None]] = {i: ({}, None) for i in range(len(spec.edges))}
    groups = list(_walk(spec.groups))
    containing = _containing_groups(spec)

    pairs: dict[frozenset, list[int]] = {}
    for index, edge in enumerate(spec.edges):
        if edge.source != edge.target:
            pairs.setdefault(frozenset((edge.source, edge.target)), []).append(index)
    shared = set()
    for indices in (i for i in pairs.values() if len(i) > 1):
        first = spec.edges[indices[0]]
        for k, index in enumerate(indices):
            edge = spec.edges[index]
            source, target = _absolute(plan, edge.source), _absolute(plan, edge.target)
            spread = -0.4 + 0.8 * k / (len(indices) - 1)
            backwards = (edge.source, edge.target) != (first.source, first.target)
            extras[index] = (_facing_constraints(source, target, (k + 1) / (len(indices) + 1)),
                             -spread if backwards else spread)
            plan.edge_points[index] = []
            shared.add(index)

    for index, edge in enumerate(spec.edges):
        if index in shared or edge.source == edge.target:
            continue
        ends = {edge.source, edge.target}
        obstacles = [_absolute(plan, n.id) for n in spec.nodes
                     if n.id not in ends and not (containing[n.id] & ends)]
        obstacles += [_absolute(plan, g.id) for g in groups
                      if g.id not in ends and not ({edge.source, edge.target} & _members_deep(g))]
        source, target = _absolute(plan, edge.source), _absolute(plan, edge.target)
        ox, oy = _origin(plan, plan.edge_parent[index])
        waypoints = [(ox + x, oy + y) for x, y in plan.edge_points[index]]
        if route_crosses(default_route(source, target, waypoints), obstacles):
            detour = route_around(source, target, obstacles)
            if detour:
                plan.edge_points[index] = [(x - ox, y - oy) for x, y in detour]
    return extras


def _facing_constraints(source: Rect, target: Rect, slot: float) -> dict[str, object]:
    dx, dy = target.cx - source.cx, target.cy - source.cy
    slot = round(slot, 3)
    if abs(dy) * source.w >= abs(dx) * source.h:
        down = dy >= 0
        exit_point, entry_point = (slot, 1 if down else 0), (slot, 0 if down else 1)
    else:
        right = dx >= 0
        exit_point, entry_point = (1 if right else 0, slot), (0 if right else 1, slot)
    return {"exitX": exit_point[0], "exitY": exit_point[1], "exitDx": 0, "exitDy": 0,
            "entryX": entry_point[0], "entryY": entry_point[1], "entryDx": 0, "entryDy": 0}


def _absolute(plan: Plan, element: str) -> Rect:
    placed = plan.nodes.get(element) or plan.groups[element]
    x, y = _origin(plan, placed.parent)
    return Rect(x + placed.x, y + placed.y, placed.width, placed.height)


def _origin(plan: Plan, group: str | None) -> tuple[float, float]:
    if group is ROOT:
        return 0.0, 0.0
    box = _absolute(plan, group)
    return box.x, box.y


def _containing_groups(spec: GraphSpec) -> dict[str, set[str]]:
    """Every group that holds each node, at any depth."""
    holders: dict[str, set[str]] = {n.id: set() for n in spec.nodes}

    def visit(group: Group, outer: set[str]) -> None:
        chain = outer | {group.id}
        for member in group.members:
            holders[member] |= chain
        for nested in group.groups:
            visit(nested, chain)

    for group in spec.groups:
        visit(group, set())
    return holders


def _members_deep(group: Group) -> set[str]:
    found = set(group.members)
    for nested in group.groups:
        found |= {nested.id} | _members_deep(nested)
    return found


def measure(node: Node, direction: str = "TD") -> Box:
    shape = node.shape
    if shape in ("start", "end"):
        return Box(30, 30)
    if shape == "fork":
        return Box(10, 80) if direction in ("LR", "RL") else Box(80, 10)
    if shape == "class":
        return _measure_rows(_class_title(node), node.attributes + node.methods, min_width=140,
                             header=_class_header(node), row=CLASS_ROW_HEIGHT,
                             extra=DIVIDER_HEIGHT + (0 if node.attributes else CLASS_ROW_HEIGHT / 2))
    if shape == "entity":
        return _measure_rows(node.label, [_entity_row(a) for a in node.attributes], min_width=160,
                             header=ROW_HEIGHT, row=ROW_HEIGHT)
    width, height = fit_box(node.label)
    if shape == "rhombus":
        width, height = fit_box(node.label, max_width=160)
        return Box(max(120, round_up(width * 1.4)), max(80, round_up(height * 1.6)))
    if shape in ("circle", "doublecircle"):
        side = max(60, width, height)
        return Box(side, side)
    if shape == "cylinder":
        return Box(width, max(60, height + 20))
    if shape in ("hexagon", "parallelogram", "trapezoid", "asymmetric", "stadium"):
        return Box(round_up(width + 30), height)
    return Box(width, height)


def _measure_rows(title: str, rows: list[str], min_width: float, header: float, row: float,
                  extra: float = 0) -> Box:
    widest = max([text_width(title) + 30] + [text_width(r) + 20 for r in rows])
    return Box(round_up(max(min_width, widest)), header + row * len(rows) + extra)


def _class_title(node: Node) -> str:
    return f"«{node.stereotype}»\n{node.label}" if node.stereotype else node.label


def _class_header(node: Node) -> float:
    return 40 if node.stereotype else ROW_HEIGHT


def _entity_row(attribute: dict[str, str]) -> str:
    key = f"{attribute['key']}  " if attribute["key"] else ""
    kind = f": {attribute['type']}" if attribute["type"] else ""
    return f"{key}{attribute['name']}{kind}"


def _node_style(node: Node, spec: GraphSpec) -> str:
    base = SHAPE_STYLES[node.shape]
    colours = dict(SHAPE_COLOURS.get(node.shape, PRIMARY))
    overrides = {}
    for css in (spec.classes.get(node.cls, {}) if node.cls else {}), node.style:
        for key, value in css.items():
            if key in CSS_TO_STYLE:
                overrides[CSS_TO_STYLE[key]] = str(value).replace("px", "")
            elif key == "stroke-dasharray":
                overrides["dashed"] = "1"
            elif key == "font-weight" and str(value) in ("bold", "700"):
                overrides["fontStyle"] = "1"
    colours.update(overrides)
    return base + style_string(**colours)


def _emit_node(builder: DrawioBuilder, node: Node, cell_id: str, placed: Placed, parent: str, spec: GraphSpec) -> None:
    if node.shape in ("class", "entity"):
        _emit_table(builder, node, cell_id, placed, parent)
        return
    label = "" if node.shape in ("start", "end", "fork") else html_label(node.label)
    builder.vertex(cell_id, label, _node_style(node, spec), parent, placed.x, placed.y, placed.width, placed.height)


def _emit_table(builder: DrawioBuilder, node: Node, cell_id: str, placed: Placed, parent: str) -> None:
    if node.shape == "class":
        title = _class_title(node).split("\n")
        value = "<br>".join([html_label(t) for t in title[:-1]] + [f"<b>{html_label(title[-1])}</b>"])
        header, row_height = _class_header(node), CLASS_ROW_HEIGHT
        sections = [[(a, False) for a in node.attributes or [""]], [(m, False) for m in node.methods]]
    else:
        value, header, row_height = html_label(node.label), ROW_HEIGHT, ROW_HEIGHT
        sections = [[(_entity_row(a), "PK" in a["key"]) for a in node.attributes]]
    builder.vertex(cell_id, value, TABLE_STYLE.format(header=header), parent,
                   placed.x, placed.y, placed.width, placed.height)
    y = header
    for s, rows in enumerate(sections):
        if s:
            builder.vertex(builder.new_id(f"{cell_id}-divider"), "", DIVIDER_STYLE, cell_id, 0, y, placed.width, DIVIDER_HEIGHT)
            y += DIVIDER_HEIGHT
        for r, (text, bold) in enumerate(rows):
            height = row_height if text or node.shape == "entity" else row_height / 2
            builder.vertex(builder.new_id(f"{cell_id}-row-{s}-{r}"), html_label(text), ROW_STYLE + ("fontStyle=1;" if bold else ""),
                           cell_id, 0, y, placed.width, height)
            y += height


def _edge_style(edge: Edge) -> str:
    end, end_fill = MARKERS[edge.head]
    start, start_fill = MARKERS[edge.tail]
    line = {"dotted": {"dashed": "1"}, "thick": {"strokeWidth": "3"}, "invisible": {"strokeColor": "none"}}.get(edge.line, {})
    sizes = {"endSize": "10"} if end.startswith("ER") else {}
    sizes.update({"startSize": "10"} if start.startswith("ER") else {})
    return style_string(edgeStyle="orthogonalEdgeStyle", rounded="1", html="1", endArrow=end, endFill=end_fill,
                        startArrow=start, startFill=start_fill, strokeColor=line.get("strokeColor", "#666666"),
                        dashed=line.get("dashed"), strokeWidth=line.get("strokeWidth"), **sizes)


def _emit_edge(builder: DrawioBuilder, index: int, edge: Edge, cell_id: dict[str, str], parent: str,
               points: list[tuple[float, float]], extra_style: dict[str, object],
               label_position: float | None) -> None:
    edge_id = builder.new_id(f"edge-{index}")
    builder.edge(edge_id, html_label(edge.label), _edge_style(edge) + style_string(**extra_style), parent,
                 source=cell_id[edge.source], target=cell_id[edge.target], points=points,
                 label_position=label_position if edge.label else None)
    for text, position in ((edge.source_label, -0.8), (edge.target_label, 0.8)):
        if text:
            builder.edge_label(builder.new_id(f"{edge_id}-label"), html_label(text), edge_id, position)


def _walk(groups: list[Group]):
    for group in groups:
        yield group
        yield from _walk(group.groups)


def _walk_with_parent(groups: list[Group], parent: str | None):
    for group in groups:
        yield group, parent
        yield from _walk_with_parent(group.groups, group.id)


def _top_down(groups: list[Group]) -> list[str]:
    return [g.id for g in _walk(groups)]
