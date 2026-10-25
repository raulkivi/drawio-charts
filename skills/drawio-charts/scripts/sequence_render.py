"""Sequence specs -> draw.io cells.

Participants become umlLifeline columns; items are placed top to bottom.
Messages attach to the lifeline (or its activation bar, when active) with
exitDy/entryDy offsets, so they keep their height when edited in draw.io.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from drawio_writer import DrawioBuilder, html_label, style_string
from graph_spec import Activation, Frame, Item, Message, Note, SequenceSpec
from text_metrics import LINE_HEIGHT, round_up, text_width, wrap

TOP = 40
HEADER = 40
FIRST_ROW = 30
MESSAGE_ROW = 40
SELF_MESSAGE_ROW = 60
LIFELINE_MIN_WIDTH = 100
LIFELINE_GAP = 60
BAR_WIDTH = 10
FRAME_HEADER = 30
FRAME_MARGIN = 70

LIFELINE_STYLE = ("shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;dropTarget=0;"
                  "collapsible=0;recursiveResize=0;outlineConnect=0;portConstraint=eastwest;size=40;"
                  "fillColor=#dae8fc;strokeColor=#6c8ebf;")
ACTOR_STYLE = "participant=umlActor;"
BAR_STYLE = ("html=1;points=[];perimeter=orthogonalPerimeter;outlineConnect=0;targetShapes=umlLifeline;"
             "portConstraint=eastwest;shape=umlActivation;fillColor=#f5f5f5;strokeColor=#666666;")
NOTE_STYLE = "shape=note;whiteSpace=wrap;html=1;size=12;backgroundOutline=1;fillColor=#fff2cc;strokeColor=#d6b656;"
FRAME_STYLE = "shape=umlFrame;whiteSpace=wrap;html=1;width=60;height=26;fillColor=none;strokeColor=#666666;"
GUARD_STYLE = "text;html=1;align=left;verticalAlign=middle;fontStyle=2;whiteSpace=wrap;"
HEADS = {"arrow": ("block", 1), "open": ("open", 0), "cross": ("cross", 0), "none": ("none", 0)}


@dataclass
class Bar:
    cell: str
    participant: str
    top: float
    depth: int


@dataclass
class State:
    y: float = TOP + HEADER + FIRST_ROW
    open_bars: dict[str, list[Bar]] = field(default_factory=dict)
    done_bars: list[tuple[Bar, float]] = field(default_factory=list)
    later: list = field(default_factory=list)   # cells drawn after bars (messages on top)
    frames: list = field(default_factory=list)  # cells drawn first (behind everything)
    notes: list = field(default_factory=list)


def render_sequence(spec: SequenceSpec) -> str:
    builder = DrawioBuilder()
    width = {p.id: max(LIFELINE_MIN_WIDTH, round_up(text_width(p.label) + 30)) for p in spec.participants}
    order = [p.id for p in spec.participants]
    gaps = _column_gaps(order, spec.items, width)
    centre, x = {}, 40.0
    for i, pid in enumerate(order):
        if i:
            x += gaps[i - 1]
        centre[pid] = x + width[pid] / 2
        x += width[pid]

    lifeline = {p.id: builder.new_id(p.id) for p in spec.participants}
    state = State()
    renderer = _ItemRenderer(builder, centre, width, lifeline, state)
    renderer.items(spec.items, depth=0)
    for bars in state.open_bars.values():
        for bar in bars:
            state.done_bars.append((bar, state.y))
    bottom = state.y + 20

    for frame_cell in state.frames:
        frame_cell()
    for p in spec.participants:
        style = LIFELINE_STYLE + (ACTOR_STYLE if p.kind == "actor" else "")
        builder.vertex(lifeline[p.id], html_label(p.label), style, "1",
                       centre[p.id] - width[p.id] / 2, TOP, width[p.id], bottom - TOP)
    for bar, end in state.done_bars:
        left = width[bar.participant] / 2 - BAR_WIDTH / 2 + bar.depth * BAR_WIDTH / 2
        builder.vertex(bar.cell, "", BAR_STYLE, lifeline[bar.participant], left, bar.top - TOP,
                       BAR_WIDTH, max(end - bar.top, 20))
    for note_cell in state.notes:
        note_cell()
    for message_cell in state.later:
        message_cell()
    return builder.to_xml(spec.title or "Page-1", x + 40, bottom + 40)


def _column_gaps(order: list[str], items: list[Item], width: dict[str, float]) -> list[float]:
    """Gap after each column, wide enough for the labels of messages between neighbours."""
    gaps = [float(LIFELINE_GAP)] * max(0, len(order) - 1)
    index = {pid: i for i, pid in enumerate(order)}
    for message in _messages(items):
        a, b = sorted((index[message.source], index[message.target]))
        if a == b:
            continue
        needed = text_width(message.label) + 30 - sum(width[order[i]] / 2 + width[order[i + 1]] / 2 for i in range(a, b))
        if needed > sum(gaps[a:b]):
            extra = (needed - sum(gaps[a:b])) / (b - a)
            for i in range(a, b):
                gaps[i] += round_up(extra)
    return gaps


def _messages(items: list[Item]):
    for item in items:
        if isinstance(item, Message):
            yield item
        elif isinstance(item, Frame):
            for section in item.sections:
                yield from _messages(section.items)


def _participants_in(items: list[Item]) -> set[str]:
    found: set[str] = set()
    for item in items:
        if isinstance(item, Message):
            found |= {item.source, item.target}
        elif isinstance(item, Note):
            found |= set(item.over)
        elif isinstance(item, Activation):
            found.add(item.participant)
        elif isinstance(item, Frame):
            for section in item.sections:
                found |= _participants_in(section.items)
    return found


class _ItemRenderer:
    def __init__(self, builder: DrawioBuilder, centre: dict[str, float], width: dict[str, float],
                 lifeline: dict[str, str], state: State) -> None:
        self.b, self.centre, self.width, self.lifeline, self.s = builder, centre, width, lifeline, state

    def items(self, items: list[Item], depth: int) -> None:
        for item in items:
            if isinstance(item, Message):
                self.message(item)
            elif isinstance(item, Note):
                self.note(item)
            elif isinstance(item, Activation):
                (self.activate if item.on else self.deactivate)(item.participant)
            elif isinstance(item, Frame):
                self.frame(item, depth)

    def activate(self, participant: str) -> None:
        bars = self.s.open_bars.setdefault(participant, [])
        bars.append(Bar(self.b.new_id(f"{participant}-active"), participant, self.s.y, len(bars)))

    def deactivate(self, participant: str) -> None:
        bars = self.s.open_bars.get(participant)
        if bars:
            self.s.done_bars.append((bars.pop(), self.s.y))

    def anchor(self, participant: str, towards_right: bool) -> tuple[str, float, float]:
        """Cell to attach to, its exit/entry X, and its absolute top."""
        bars = self.s.open_bars.get(participant)
        if bars:
            return bars[-1].cell, (1 if towards_right else 0), bars[-1].top
        return self.lifeline[participant], 0.5, TOP

    def message(self, m: Message) -> None:
        y = self.s.y
        self_call = m.source == m.target
        rightwards = self_call or self.centre[m.target] > self.centre[m.source]
        source, exit_x, source_top = self.anchor(m.source, rightwards)
        if m.activate and not self_call:
            self.activate(m.target)
        target, entry_x, target_top = self.anchor(m.target, not rightwards)
        end_y = y + (30 if self_call else 0)
        end, filled = HEADS[m.head]
        style = style_string(html="1", verticalAlign="bottom", endArrow=end, endFill=filled, curved="0", rounded="0",
                             dashed="1" if m.line == "dotted" else None, align="left" if self_call else None,
                             exitX=exit_x, exitY="0", exitDx="0", exitDy=round(y - source_top),
                             entryX=entry_x if not self_call else 1 if entry_x != 0.5 else 0.5,
                             entryY="0", entryDx="0", entryDy=round(end_y - target_top))
        points = []
        if self_call:
            x = self.centre[m.source] + 40
            points = [(x, y), (x, end_y)]
        cell_id = self.b.new_id("msg")
        self.s.later.append(lambda: self.b.edge(cell_id, html_label(m.label), style, "1", source=source,
                                                target=target, points=points))
        if m.deactivate:
            self.deactivate(m.source)
        self.s.y += SELF_MESSAGE_ROW if self_call else MESSAGE_ROW

    def note(self, n: Note) -> None:
        lines = wrap(n.text.split("\n"), 160)
        height = max(30, round_up(len(lines) * LINE_HEIGHT + 14))
        xs = [self.centre[p] for p in n.over]
        text_w = max(100, round_up(max(text_width(line) for line in lines) + 24))
        if n.position == "over":
            left = min(xs) - 50 if len(xs) > 1 else xs[0] - text_w / 2
            right = max(xs) + 50 if len(xs) > 1 else xs[0] + text_w / 2
        elif n.position == "left of":
            right = min(xs) - 10
            left = right - text_w
        else:
            left = max(xs) + 10
            right = left + text_w
        y = self.s.y - 10
        cell_id = self.b.new_id("note")
        self.s.notes.append(lambda: self.b.vertex(cell_id, html_label(n.text), NOTE_STYLE, "1",
                                                  left, y, right - left, height))
        self.s.y += height + 10

    def frame(self, f: Frame, depth: int) -> None:
        involved = _participants_in([f]) or set(self.centre)
        margin = max(FRAME_MARGIN - 10 * depth, 20)  # nested frames sit inside their parent
        left = min(self.centre[p] for p in involved) - margin
        right = max(self.centre[p] for p in involved) + margin
        top = self.s.y - 20
        frame_id = self.b.new_id(f"frame-{f.kind}")
        self.s.y = top + FRAME_HEADER + 20
        for i, section in enumerate(f.sections):
            section_top = self.s.y - 20 if i else top
            if i:
                y_line = section_top
                line_id = self.b.new_id("frame-divider")
                self.s.frames.append(lambda y_line=y_line, line_id=line_id: self.b.edge(
                    line_id, "", "endArrow=none;dashed=1;html=1;strokeColor=#666666;", "1",
                    source_point=(left, y_line), target_point=(right, y_line)))
                self.s.y += 10
            if section.label:
                guard_x = left + (65 if not i else 10)
                guard_y = (top + 2) if not i else section_top + 2
                guard_id = self.b.new_id("guard")
                label = html_label(f"[{section.label}]")
                self.s.frames.append(lambda guard_id=guard_id, label=label, gx=guard_x, gy=guard_y: self.b.vertex(
                    guard_id, label, GUARD_STYLE, "1", gx, gy, max(80, right - gx - 10), 22))
            self.items(section.items, depth + 1)
        bottom = self.s.y - 10
        self.s.frames.insert(0, lambda: self.b.vertex(frame_id, f.kind, FRAME_STYLE, "1", left, top, right - left,
                                                      bottom - top))
        self.s.y = bottom + 30
