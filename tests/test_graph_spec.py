import unittest

from helpers import SCRIPTS_DIR  # noqa: F401  (puts scripts/ on sys.path)

from graph_spec import (
    Frame, GraphSpec, Message, Note, SequenceSpec, SpecError, parse_spec,
)


def flowchart(**overrides):
    spec = {
        "type": "flowchart",
        "nodes": [{"id": "A"}, {"id": "B", "label": "Bee", "shape": "rhombus"}],
        "edges": [{"from": "A", "to": "B"}],
    }
    spec.update(overrides)
    return spec


class GraphSpecTest(unittest.TestCase):
    def test_defaults(self):
        spec = parse_spec(flowchart())
        self.assertIsInstance(spec, GraphSpec)
        self.assertEqual(spec.direction, "TD")
        a, b = spec.nodes
        self.assertEqual((a.label, a.shape), ("A", "rect"))
        self.assertEqual((b.label, b.shape), ("Bee", "rhombus"))
        edge = spec.edges[0]
        self.assertEqual((edge.source, edge.target), ("A", "B"))
        self.assertEqual((edge.line, edge.head, edge.tail, edge.label), ("solid", "arrow", "none", ""))

    def test_tb_is_an_alias_for_td(self):
        self.assertEqual(parse_spec(flowchart(direction="TB")).direction, "TD")

    def test_nested_groups(self):
        spec = parse_spec(flowchart(groups=[
            {"id": "outer", "label": "Outer", "members": ["A"],
             "groups": [{"id": "inner", "members": ["B"]}]},
        ]))
        outer = spec.groups[0]
        self.assertEqual((outer.id, outer.label, outer.members), ("outer", "Outer", ["A"]))
        self.assertEqual(outer.groups[0].members, ["B"])
        self.assertEqual(outer.groups[0].label, "inner")

    def test_edge_may_target_a_group(self):
        spec = parse_spec(flowchart(groups=[{"id": "g", "members": ["B"]}],
                                    edges=[{"from": "A", "to": "g"}]))
        self.assertEqual(spec.edges[0].target, "g")

    def test_class_and_entity_details(self):
        spec = parse_spec({
            "type": "class",
            "nodes": [{"id": "Order", "shape": "class", "stereotype": "entity",
                       "attributes": ["+id: int"], "methods": ["+total() float"]}],
        })
        node = spec.nodes[0]
        self.assertEqual((node.attributes, node.methods, node.stereotype), (["+id: int"], ["+total() float"], "entity"))

        er = parse_spec({
            "type": "er",
            "nodes": [{"id": "USER", "shape": "entity",
                       "attributes": [{"name": "id", "type": "int", "key": "PK"}, {"name": "email"}]}],
        })
        self.assertEqual(er.nodes[0].attributes[0], {"name": "id", "type": "int", "key": "PK"})
        self.assertEqual(er.nodes[0].attributes[1], {"name": "email", "type": "", "key": ""})

    def test_class_styles(self):
        spec = parse_spec(flowchart(classes={"hot": {"fill": "#f8cecc", "stroke": "#b85450"}},
                                    nodes=[{"id": "A", "class": "hot"}, {"id": "B"}]))
        self.assertEqual(spec.classes["hot"]["fill"], "#f8cecc")
        self.assertEqual(spec.nodes[0].cls, "hot")

    def assertSpecError(self, data, fragment):
        with self.assertRaises(SpecError) as caught:
            parse_spec(data)
        self.assertIn(fragment, str(caught.exception))

    def test_errors(self):
        self.assertSpecError({"type": "gantt"}, "type")
        self.assertSpecError(flowchart(direction="UP"), "direction")
        self.assertSpecError(flowchart(nodes=[{"id": "A"}, {"id": "A"}]), "duplicate")
        self.assertSpecError(flowchart(nodes=[{"id": "A", "shape": "blob"}, {"id": "B"}]), "shape")
        self.assertSpecError(flowchart(edges=[{"from": "A", "to": "Z"}]), '"Z"')
        self.assertSpecError(flowchart(edges=[{"from": "A", "to": "B", "head": "spear"}]), "head")
        self.assertSpecError(flowchart(edges=[{"from": "A", "to": "B", "line": "wavy"}]), "line")
        self.assertSpecError(flowchart(groups=[{"id": "g", "members": ["Z"]}]), '"Z"')
        self.assertSpecError(flowchart(groups=[{"id": "g", "members": ["A"]}, {"id": "h", "members": ["A"]}]), "more than one group")
        self.assertSpecError(flowchart(groups=[{"id": "A", "members": ["B"]}]), "duplicate")
        self.assertSpecError(flowchart(nodes=[{"id": "A", "class": "nope"}, {"id": "B"}]), "class")
        self.assertSpecError(flowchart(nodes=[{"label": "no id"}]), "id")
        self.assertSpecError([], "object")


class SequenceSpecTest(unittest.TestCase):
    def test_parse_items(self):
        spec = parse_spec({
            "type": "sequence",
            "participants": [{"id": "U", "label": "User", "kind": "actor"}, {"id": "S"}],
            "items": [
                {"message": {"from": "U", "to": "S", "label": "hi", "activate": True}},
                {"note": {"over": ["U", "S"], "text": "both"}},
                {"frame": {"kind": "alt", "sections": [
                    {"label": "ok", "items": [{"message": {"from": "S", "to": "U", "line": "dotted", "deactivate": True}}]},
                    {"label": "else", "items": []},
                ]}},
                {"activate": "U"},
                {"deactivate": "U"},
            ],
        })
        self.assertIsInstance(spec, SequenceSpec)
        self.assertEqual([p.kind for p in spec.participants], ["actor", "participant"])
        self.assertEqual(spec.participants[1].label, "S")
        message, note, frame, activate, deactivate = spec.items
        self.assertIsInstance(message, Message)
        self.assertTrue(message.activate)
        self.assertEqual((message.line, message.head), ("solid", "arrow"))
        self.assertIsInstance(note, Note)
        self.assertEqual((note.over, note.position), (["U", "S"], "over"))
        self.assertIsInstance(frame, Frame)
        self.assertEqual([s.label for s in frame.sections], ["ok", "else"])
        self.assertTrue(frame.sections[0].items[0].deactivate)
        self.assertEqual((activate.participant, activate.on), ("U", True))
        self.assertEqual((deactivate.participant, deactivate.on), ("U", False))

    def test_errors(self):
        base = {"type": "sequence", "participants": [{"id": "A"}]}
        with self.assertRaisesRegex(SpecError, '"B"'):
            parse_spec({**base, "items": [{"message": {"from": "A", "to": "B"}}]})
        with self.assertRaisesRegex(SpecError, "kind"):
            parse_spec({**base, "items": [{"frame": {"kind": "maybe", "sections": []}}]})
        with self.assertRaisesRegex(SpecError, "item"):
            parse_spec({**base, "items": [{"dance": {}}]})
        with self.assertRaisesRegex(SpecError, "position"):
            parse_spec({**base, "items": [{"note": {"over": ["A"], "position": "under", "text": "x"}}]})


if __name__ == "__main__":
    unittest.main()
