"""The graph spec: a small JSON format between a Mermaid diagram and the layout.

Claude reads the Mermaid source and writes this spec; layout_drawio.py turns
it into a .drawio file. See references/mermaid-mapping.md for the format.
parse_spec() checks it fully, so the layout code can trust what it gets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union

GRAPH_TYPES = ("flowchart", "state", "class", "er")
DIRECTIONS = {"TD": "TD", "TB": "TD", "BT": "BT", "LR": "LR", "RL": "RL"}
SHAPES = (
    "rect", "rounded", "stadium", "subroutine", "cylinder", "circle", "doublecircle",
    "rhombus", "hexagon", "parallelogram", "trapezoid", "asymmetric", "text",
    "start", "end", "fork", "note", "class", "entity",
)
LINES = ("solid", "dotted", "thick", "invisible")
MARKERS = (
    "none", "arrow", "open", "triangle", "diamond", "odiamond", "circle", "cross",
    "one", "zero_or_one", "one_or_more", "zero_or_more",
)
SEQUENCE_HEADS = ("arrow", "open", "cross", "none")
FRAME_KINDS = ("loop", "alt", "opt", "par", "critical", "break", "rect")
NOTE_POSITIONS = ("over", "left of", "right of")
PARTICIPANT_KINDS = ("participant", "actor")


class SpecError(ValueError):
    """The spec is not valid; the message says where and why."""


@dataclass
class Node:
    id: str
    label: str
    shape: str = "rect"
    cls: str | None = None
    style: dict[str, str] = field(default_factory=dict)
    attributes: list[Any] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    stereotype: str | None = None


@dataclass
class Edge:
    source: str
    target: str
    label: str = ""
    line: str = "solid"
    head: str = "arrow"
    tail: str = "none"
    source_label: str = ""
    target_label: str = ""


@dataclass
class Group:
    id: str
    label: str
    members: list[str] = field(default_factory=list)
    groups: list[Group] = field(default_factory=list)


@dataclass
class GraphSpec:
    type: str
    direction: str
    nodes: list[Node]
    edges: list[Edge]
    groups: list[Group]
    classes: dict[str, dict[str, str]]
    title: str = ""


@dataclass
class Participant:
    id: str
    label: str
    kind: str = "participant"


@dataclass
class Message:
    source: str
    target: str
    label: str = ""
    line: str = "solid"
    head: str = "arrow"
    activate: bool = False
    deactivate: bool = False


@dataclass
class Note:
    over: list[str]
    text: str
    position: str = "over"


@dataclass
class Activation:
    participant: str
    on: bool


@dataclass
class Section:
    label: str
    items: list[Item]


@dataclass
class Frame:
    kind: str
    label: str
    sections: list[Section]


Item = Union[Message, Note, Activation, Frame]


@dataclass
class SequenceSpec:
    type: str
    participants: list[Participant]
    items: list[Item]
    title: str = ""


Spec = Union[GraphSpec, SequenceSpec]


def parse_spec(data: Any) -> Spec:
    if not isinstance(data, dict):
        raise SpecError("spec must be a JSON object")
    kind = data.get("type")
    if kind == "sequence":
        return _parse_sequence(data)
    if kind in GRAPH_TYPES:
        return _parse_graph(data)
    raise SpecError(f"type must be one of {', '.join(GRAPH_TYPES + ('sequence',))}, not {kind!r}")


# --- graph types ---------------------------------------------------------

def _parse_graph(data: dict) -> GraphSpec:
    direction = DIRECTIONS.get(str(data.get("direction", "TD")).upper())
    if direction is None:
        raise SpecError(f"direction must be one of {', '.join(DIRECTIONS)}, not {data.get('direction')!r}")
    classes = data.get("classes", {}) or {}
    nodes = [_parse_node(raw, i, classes) for i, raw in enumerate(data.get("nodes", []))]
    groups = [_parse_group(raw, f"groups[{i}]") for i, raw in enumerate(data.get("groups", []))]

    ids = [n.id for n in nodes] + [g.id for g in _walk(groups)]
    _require_unique(ids, "node/group id")
    node_ids = {n.id for n in nodes}
    owner: dict[str, str] = {}
    for group in _walk(groups):
        for member in group.members:
            if member not in node_ids:
                raise SpecError(f'group "{group.id}" lists member "{member}", which is not a node')
            if member in owner:
                raise SpecError(f'node "{member}" is in more than one group ("{owner[member]}", "{group.id}")')
            owner[member] = group.id

    known = set(ids)
    edges = [_parse_edge(raw, i, known) for i, raw in enumerate(data.get("edges", []))]
    return GraphSpec(data["type"], direction, nodes, edges, groups, classes, str(data.get("title", "")))


def _parse_node(raw: Any, index: int, classes: dict) -> Node:
    where = f"nodes[{index}]"
    node_id = _require_id(raw, where)
    shape = raw.get("shape", "rect")
    if shape not in SHAPES:
        raise SpecError(f"{where}: shape must be one of {', '.join(SHAPES)}, not {shape!r}")
    cls = raw.get("class")
    if cls is not None and cls not in classes:
        raise SpecError(f'{where}: class "{cls}" is not defined in "classes"')
    attributes = raw.get("attributes", [])
    if shape == "entity":
        attributes = [_parse_attribute(a, f"{where}.attributes") for a in attributes]
    return Node(
        id=node_id,
        label=str(raw.get("label", node_id)),
        shape=shape,
        cls=cls,
        style=dict(raw.get("style", {})),
        attributes=list(attributes),
        methods=[str(m) for m in raw.get("methods", [])],
        stereotype=raw.get("stereotype"),
    )


def _parse_attribute(raw: Any, where: str) -> dict[str, str]:
    if isinstance(raw, str):
        raw = {"name": raw}
    if not isinstance(raw, dict) or not raw.get("name"):
        raise SpecError(f"{where}: each attribute needs a name")
    return {"name": str(raw["name"]), "type": str(raw.get("type", "")), "key": str(raw.get("key", ""))}


def _parse_group(raw: Any, where: str) -> Group:
    group_id = _require_id(raw, where)
    nested = [_parse_group(g, f"{where}.groups[{i}]") for i, g in enumerate(raw.get("groups", []))]
    return Group(group_id, str(raw.get("label", group_id)), [str(m) for m in raw.get("members", [])], nested)


def _parse_edge(raw: Any, index: int, known: set[str]) -> Edge:
    where = f"edges[{index}]"
    if not isinstance(raw, dict):
        raise SpecError(f"{where}: must be an object")
    for end in ("from", "to"):
        if raw.get(end) not in known:
            raise SpecError(f'{where}: "{end}" refers to "{raw.get(end)}", which is not a node or group')
    edge = Edge(
        source=raw["from"], target=raw["to"], label=str(raw.get("label", "")),
        line=raw.get("line", "solid"), head=raw.get("head", "arrow"), tail=raw.get("tail", "none"),
        source_label=str(raw.get("fromLabel", "")), target_label=str(raw.get("toLabel", "")),
    )
    if edge.line not in LINES:
        raise SpecError(f"{where}: line must be one of {', '.join(LINES)}, not {edge.line!r}")
    for end, marker in (("head", edge.head), ("tail", edge.tail)):
        if marker not in MARKERS:
            raise SpecError(f"{where}: {end} must be one of {', '.join(MARKERS)}, not {marker!r}")
    return edge


def _walk(groups: list[Group]):
    for group in groups:
        yield group
        yield from _walk(group.groups)


# --- sequence ------------------------------------------------------------

def _parse_sequence(data: dict) -> SequenceSpec:
    participants = []
    for i, raw in enumerate(data.get("participants", [])):
        pid = _require_id(raw, f"participants[{i}]")
        kind = raw.get("kind", "participant")
        if kind not in PARTICIPANT_KINDS:
            raise SpecError(f"participants[{i}]: kind must be participant or actor")
        participants.append(Participant(pid, str(raw.get("label", pid)), kind))
    _require_unique([p.id for p in participants], "participant id")
    known = {p.id for p in participants}
    items = _parse_items(data.get("items", []), "items", known)
    return SequenceSpec("sequence", participants, items, str(data.get("title", "")))


def _parse_items(raw_items: Any, where: str, known: set[str]) -> list[Item]:
    return [_parse_item(raw, f"{where}[{i}]", known) for i, raw in enumerate(raw_items)]


def _parse_item(raw: Any, where: str, known: set[str]) -> Item:
    if not isinstance(raw, dict) or len(raw) != 1:
        raise SpecError(f"{where}: each item is an object with one key: message, note, activate, deactivate or frame")
    (key, body), = raw.items()
    if key == "message":
        for end in ("from", "to"):
            _require_participant(body.get(end), where, known)
        message = Message(body["from"], body["to"], str(body.get("label", "")), body.get("line", "solid"),
                          body.get("head", "arrow"), bool(body.get("activate")), bool(body.get("deactivate")))
        if message.line not in ("solid", "dotted"):
            raise SpecError(f"{where}: line must be solid or dotted")
        if message.head not in SEQUENCE_HEADS:
            raise SpecError(f"{where}: head must be one of {', '.join(SEQUENCE_HEADS)}")
        return message
    if key == "note":
        over = body.get("over", [])
        over = [over] if isinstance(over, str) else list(over)
        if not over:
            raise SpecError(f"{where}: note needs at least one participant in \"over\"")
        for participant in over:
            _require_participant(participant, where, known)
        position = body.get("position", "over")
        if position not in NOTE_POSITIONS:
            raise SpecError(f"{where}: note position must be one of {', '.join(NOTE_POSITIONS)}")
        return Note(over, str(body.get("text", "")), position)
    if key in ("activate", "deactivate"):
        _require_participant(body, where, known)
        return Activation(body, key == "activate")
    if key == "frame":
        kind = body.get("kind")
        if kind not in FRAME_KINDS:
            raise SpecError(f"{where}: frame kind must be one of {', '.join(FRAME_KINDS)}, not {kind!r}")
        sections = [
            Section(str(s.get("label", "")), _parse_items(s.get("items", []), f"{where}.sections[{i}].items", known))
            for i, s in enumerate(body.get("sections", []))
        ]
        return Frame(kind, str(body.get("label", sections[0].label if sections else "")), sections)
    raise SpecError(f"{where}: unknown item {key!r}")


def _require_participant(value: Any, where: str, known: set[str]) -> None:
    if value not in known:
        raise SpecError(f'{where}: "{value}" is not a participant')


# --- shared --------------------------------------------------------------

def _require_id(raw: Any, where: str) -> str:
    if not isinstance(raw, dict) or not raw.get("id"):
        raise SpecError(f"{where}: needs an id")
    return str(raw["id"])


def _require_unique(ids: list[str], what: str) -> None:
    seen = set()
    for value in ids:
        if value in seen:
            raise SpecError(f'duplicate {what} "{value}"')
        seen.add(value)
