import io
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stderr
from pathlib import Path

from helpers import SCRIPTS_DIR  # noqa: F401

import layout_drawio
from drawio_io import cells, parse_pages
from validate_drawio import validate_string

FLOWCHART = {
    "type": "flowchart",
    "direction": "TD",
    "classes": {"hot": {"fill": "#f8cecc", "stroke": "#b85450", "color": "#333333"}},
    "nodes": [
        {"id": "start", "label": "Order placed", "shape": "stadium"},
        {"id": "pay", "label": "Payment ok?", "shape": "rhombus"},
        {"id": "pick", "label": "Pick items"},
        {"id": "pack", "label": "Pack"},
        {"id": "db", "label": "Orders DB", "shape": "cylinder"},
        {"id": "fail", "label": "Email customer & cancel", "class": "hot"},
    ],
    "edges": [
        {"from": "start", "to": "pay"},
        {"from": "pay", "to": "pick", "label": "yes"},
        {"from": "pay", "to": "fail", "label": "no", "line": "dotted"},
        {"from": "pick", "to": "pack", "line": "thick"},
        {"from": "pack", "to": "db", "head": "none"},
        {"from": "start", "to": "warehouse"},
    ],
    "groups": [
        {"id": "warehouse", "label": "Warehouse", "members": ["pick"],
         "groups": [{"id": "packing", "label": "Packing", "members": ["pack"]}]},
    ],
}

SEQUENCE = {
    "type": "sequence",
    "participants": [{"id": "U", "label": "User", "kind": "actor"}, {"id": "API"}, {"id": "DB", "label": "Orders DB"}],
    "items": [
        {"message": {"from": "U", "to": "API", "label": "POST /orders", "activate": True}},
        {"message": {"from": "API", "to": "API", "label": "validate"}},
        {"frame": {"kind": "alt", "label": "valid", "sections": [
            {"label": "valid", "items": [
                {"message": {"from": "API", "to": "DB", "label": "INSERT"}},
                {"message": {"from": "DB", "to": "API", "label": "id", "line": "dotted", "head": "open"}},
            ]},
            {"label": "invalid", "items": [{"note": {"over": ["API"], "position": "right of", "text": "400"}}]},
        ]}},
        {"message": {"from": "API", "to": "U", "label": "201", "line": "dotted", "deactivate": True}},
        {"note": {"over": ["U", "DB"], "text": "done"}},
    ],
}

CLASS = {
    "type": "class",
    "nodes": [
        {"id": "Shape", "shape": "class", "stereotype": "interface", "methods": ["+area() float"]},
        {"id": "Circle", "shape": "class", "attributes": ["-r: float"], "methods": ["+area() float"]},
    ],
    "edges": [{"from": "Circle", "to": "Shape", "head": "triangle", "line": "dotted"}],
}

ER = {
    "type": "er",
    "direction": "LR",
    "nodes": [
        {"id": "CUSTOMER", "shape": "entity", "attributes": [{"name": "id", "type": "int", "key": "PK"}, {"name": "name", "type": "text"}]},
        {"id": "ORDER", "shape": "entity", "attributes": [{"name": "id", "type": "int", "key": "PK"}, {"name": "customer_id", "type": "int", "key": "FK"}]},
    ],
    "edges": [{"from": "CUSTOMER", "to": "ORDER", "label": "places", "tail": "one", "head": "zero_or_more"}],
}

STATE = {
    "type": "state",
    "nodes": [{"id": "s0", "shape": "start"}, {"id": "Idle", "shape": "rounded"}, {"id": "Busy", "shape": "rounded"},
              {"id": "s1", "shape": "end"}],
    "edges": [{"from": "s0", "to": "Idle"}, {"from": "Idle", "to": "Busy", "label": "job"}, {"from": "Busy", "to": "s1"}],
    "groups": [{"id": "Active", "members": ["Busy"]}],
}


def convert(spec):
    return layout_drawio.convert(layout_drawio.parse_spec(spec))


def page_cells(xml):
    return cells(parse_pages(xml)[0].model)


def by_id(xml):
    return {c.id: c for c in page_cells(xml)}


def geometry(cell):
    g = cell.geometry()
    return tuple(float(g.get(k, 0)) for k in ("x", "y", "width", "height"))


class GraphDiagramTest(unittest.TestCase):
    def test_every_type_produces_a_valid_diagram(self):
        for name, spec in (("flowchart", FLOWCHART), ("sequence", SEQUENCE), ("class", CLASS), ("er", ER), ("state", STATE)):
            with self.subTest(type=name):
                self.assertEqual(validate_string(convert(spec)), [])

    def test_groups_become_nested_containers_holding_their_members(self):
        cells_ = by_id(convert(FLOWCHART))
        self.assertEqual(cells_["warehouse"].get("parent"), "1")
        self.assertEqual(cells_["packing"].get("parent"), "warehouse")
        self.assertEqual(cells_["pick"].get("parent"), "warehouse")
        self.assertEqual(cells_["pack"].get("parent"), "packing")
        self.assertIn("container=1", cells_["warehouse"].get("style"))
        for child, container in (("pick", "warehouse"), ("packing", "warehouse"), ("pack", "packing")):
            x, y, w, h = geometry(cells_[child])
            _, _, cw, ch = geometry(cells_[container])
            with self.subTest(child=child):
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 26)  # below the container header
                self.assertLessEqual(x + w, cw)
                self.assertLessEqual(y + h, ch)

    def test_siblings_do_not_overlap(self):
        cells_ = page_cells(convert(FLOWCHART))
        vertices = [c for c in cells_ if c.is_vertex]
        for parent in {c.get("parent") for c in vertices}:
            siblings = [geometry(c) for c in vertices if c.get("parent") == parent]
            for i, (ax, ay, aw, ah) in enumerate(siblings):
                for bx, by, bw, bh in siblings[i + 1:]:
                    self.assertFalse(ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah, parent)

    def test_edges_labels_and_group_targets(self):
        xml = convert(FLOWCHART)
        edges = [c for c in page_cells(xml) if c.is_edge]
        self.assertEqual(len(edges), len(FLOWCHART["edges"]))
        labels = {(e.get("source"), e.get("target")): e.get("value") for e in edges}
        self.assertEqual(labels[("pay", "pick")], "yes")
        self.assertIn(("start", "warehouse"), labels)
        style = {(e.get("source"), e.get("target")): e.get("style") for e in edges}
        self.assertIn("dashed=1", style[("pay", "fail")])
        self.assertIn("strokeWidth=3", style[("pick", "pack")])
        self.assertIn("endArrow=none", style[("pack", "db")])

    def test_shapes_and_classes(self):
        cells_ = by_id(convert(FLOWCHART))
        self.assertIn("rhombus", cells_["pay"].get("style"))
        self.assertIn("shape=cylinder", cells_["db"].get("style"))
        self.assertIn("fillColor=#f8cecc", cells_["fail"].get("style"))
        self.assertIn("fontColor=#333333", cells_["fail"].get("style"))
        self.assertEqual(cells_["fail"].get("value"), "Email customer &amp; cancel")

    def test_class_boxes_and_relations(self):
        xml = convert(CLASS)
        cells_ = page_cells(xml)
        rows = [c.get("value") for c in cells_ if c.get("parent") == "Circle"]
        self.assertIn("-r: float", rows)
        self.assertIn("+area() float", rows)
        shape_title = by_id(xml)["Shape"].get("value")
        self.assertIn("interface", shape_title)
        edge = next(c for c in cells_ if c.is_edge)
        self.assertIn("endArrow=block", edge.get("style"))
        self.assertIn("endFill=0", edge.get("style"))
        self.assertIn("dashed=1", edge.get("style"))

    def test_er_entities_and_cardinality(self):
        xml = convert(ER)
        cells_ = page_cells(xml)
        rows = [c.get("value") for c in cells_ if c.get("parent") == "ORDER"]
        self.assertIn("FK  customer_id: int", rows)
        edge = next(c for c in cells_ if c.is_edge)
        self.assertIn("startArrow=ERmandOne", edge.get("style"))
        self.assertIn("endArrow=ERzeroToMany", edge.get("style"))
        x_customer = geometry(by_id(xml)["CUSTOMER"])[0]
        x_order = geometry(by_id(xml)["ORDER"])[0]
        self.assertLess(x_customer, x_order)  # LR

    def test_state_markers(self):
        cells_ = by_id(convert(STATE))
        self.assertIn("ellipse", cells_["s0"].get("style"))
        self.assertIn("fillColor=#000000", cells_["s0"].get("style"))
        self.assertIn("shape=endState", cells_["s1"].get("style"))
        self.assertEqual(cells_["Busy"].get("parent"), "Active")

    def test_output_is_deterministic(self):
        self.assertEqual(convert(FLOWCHART), convert(FLOWCHART))


class SequenceDiagramTest(unittest.TestCase):
    def setUp(self):
        self.xml = convert(SEQUENCE)
        self.cells = page_cells(self.xml)

    def test_one_lifeline_per_participant(self):
        lifelines = [c for c in self.cells if "shape=umlLifeline" in (c.get("style") or "")]
        self.assertEqual([c.id for c in lifelines], ["U", "API", "DB"])
        self.assertIn("participant=umlActor", by_id(self.xml)["U"].get("style"))

    def test_messages_in_order(self):
        messages = [c for c in self.cells if c.is_edge and "exitDy=" in (c.get("style") or "")]
        self.assertEqual([m.get("value") for m in messages], ["POST /orders", "validate", "INSERT", "id", "201"])
        ys = [_message_y(self.xml, m) for m in messages]
        self.assertEqual(ys, sorted(ys))
        self.assertEqual(len(set(ys)), len(ys))
        self.assertIn("dashed=1", messages[3].get("style"))
        self.assertIn("endArrow=open", messages[3].get("style"))

    def test_activation_frame_and_notes(self):
        styles = [c.get("style") or "" for c in self.cells]
        self.assertEqual(sum("umlActivation" in s for s in styles), 1)
        self.assertEqual(sum("shape=umlFrame" in s for s in styles), 1)
        self.assertEqual(sum("shape=note" in s for s in styles), 2)
        values = [c.get("value") for c in self.cells]
        self.assertIn("[invalid]", values)


def _message_y(xml, message):
    """Absolute y of a message: its lifeline/bar top plus exitDy."""
    cells_ = by_id(xml)
    source = cells_[message.get("source")]
    style = dict(part.split("=", 1) for part in message.get("style").split(";") if "=" in part)
    top = geometry(source)[1]
    parent = cells_.get(source.get("parent"))
    if parent is not None and parent.is_vertex:
        top += geometry(parent)[1]
    return top + float(style["exitDy"])


class CommandLineTest(unittest.TestCase):
    def test_writes_drawio_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, out = Path(tmp) / "spec.json", Path(tmp) / "out.drawio"
            spec.write_text(json.dumps(FLOWCHART), encoding="utf-8")
            self.assertEqual(layout_drawio.main([str(spec), "-o", str(out)]), 0)
            self.assertEqual(validate_string(out.read_text(encoding="utf-8")), [])
            ET.fromstring(out.read_text(encoding="utf-8"))

    def test_invalid_spec_exits_2_with_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "spec.json"
            spec.write_text(json.dumps({"type": "flowchart", "nodes": [], "edges": [{"from": "a", "to": "b"}]}), encoding="utf-8")
            err = io.StringIO()
            with redirect_stderr(err):
                code = layout_drawio.main([str(spec), "-o", str(Path(tmp) / "x.drawio")])
            self.assertEqual(code, 2)
            self.assertIn('"a"', err.getvalue())


if __name__ == "__main__":
    unittest.main()
