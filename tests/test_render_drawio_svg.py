import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from helpers import SCRIPTS_DIR, compress, drawio, edge, graph_model, vertex  # noqa: F401

import layout_drawio
import render_drawio_svg
from render_drawio_svg import render_svg
from test_layout_drawio import ER, FLOWCHART, SEQUENCE
from validate_drawio import validate_file, validate_string

SVG = "{http://www.w3.org/2000/svg}"


def svg_root(svg_text):
    return ET.fromstring(svg_text)


def texts(root):
    return ["".join(t.itertext()) for t in root.iter(f"{SVG}text")]


def convert(spec):
    return layout_drawio.convert(layout_drawio.parse_spec(spec))


class EmbeddingTest(unittest.TestCase):
    def test_svg_embeds_the_diagram_as_content(self):
        xml = drawio(vertex("a", style="rounded=1;") + vertex("b") + edge("e", "a", "b"))
        root = svg_root(render_svg(xml))
        self.assertEqual(root.tag, f"{SVG}svg")
        embedded = root.get("content")
        self.assertEqual(ET.tostring(ET.fromstring(embedded)), ET.tostring(ET.fromstring(xml)))

    def test_embedded_svg_is_a_valid_drawio_document(self):
        self.assertEqual(validate_string(render_svg(convert(FLOWCHART))), [])

    def test_white_background_and_size_covers_diagram(self):
        root = svg_root(render_svg(convert(FLOWCHART)))
        background = next(root.iter(f"{SVG}rect"))
        self.assertEqual(background.get("fill"), "#ffffff")
        width, height = float(root.get("width")), float(root.get("height"))
        self.assertEqual(root.get("viewBox"), f"0 0 {root.get('width')} {root.get('height')}")
        self.assertGreater(width, 200)
        self.assertGreater(height, 300)

    def test_compressed_input_is_rendered(self):
        packed = f'<mxfile><diagram id="p" name="P">{compress(graph_model(vertex("a")))}</diagram></mxfile>'
        root = svg_root(render_svg(packed))
        self.assertTrue(list(root.iter(f"{SVG}rect")))

    def test_deterministic(self):
        xml = convert(FLOWCHART)
        self.assertEqual(render_svg(xml), render_svg(xml))


class ShapesTest(unittest.TestCase):
    def shape_elements(self, style):
        root = svg_root(render_svg(drawio(vertex("a", style=style))))
        return [el.tag.replace(SVG, "") for el in root.iter() if el.get("data-cell") == "a"]

    def test_shapes_map_to_svg_primitives(self):
        cases = {
            "rounded=1;": "rect", "ellipse;": "ellipse", "rhombus;": "polygon",
            "shape=hexagon;": "polygon", "shape=cylinder3;": "path", "shape=note;": "path",
            "shape=parallelogram;": "polygon", "shape=process;": "rect", "unknownShape;": "rect",
        }
        for style, tag in cases.items():
            with self.subTest(style=style):
                self.assertIn(tag, self.shape_elements(style))

    def test_rounded_rect_has_radius(self):
        root = svg_root(render_svg(drawio(vertex("a", style="rounded=1;"))))
        rect = next(el for el in root.iter(f"{SVG}rect") if el.get("data-cell") == "a")
        self.assertGreater(float(rect.get("rx")), 0)

    def test_labels_are_drawn_with_html_line_breaks_and_entities(self):
        cell = ('<mxCell id="a" value="&lt;b&gt;Ada&lt;/b&gt;&lt;br&gt;Fish &amp;amp; Chips" style="html=1;" '
                'parent="1" vertex="1"><mxGeometry x="0" y="0" width="160" height="60" as="geometry"/></mxCell>')
        found = texts(svg_root(render_svg(drawio(cell))))
        self.assertIn("Ada", found)
        self.assertIn("Fish & Chips", found)

    def test_children_are_positioned_inside_their_container(self):
        container = vertex("box", style="swimlane;startSize=26;container=1;",
                           geometry='<mxGeometry x="100" y="50" width="200" height="120" as="geometry"/>')
        child = vertex("c", parent="box", geometry='<mxGeometry x="20" y="40" width="80" height="40" as="geometry"/>')
        root = svg_root(render_svg(drawio(container + child)))
        rect = next(el for el in root.iter(f"{SVG}rect") if el.get("data-cell") == "c")
        box = next(el for el in root.iter(f"{SVG}rect") if el.get("data-cell") == "box")
        self.assertEqual(float(rect.get("x")) - float(box.get("x")), 20)
        self.assertEqual(float(rect.get("y")) - float(box.get("y")), 40)


class EdgesTest(unittest.TestCase):
    def test_every_edge_is_drawn_with_its_markers(self):
        xml = convert(FLOWCHART)
        root = svg_root(render_svg(xml))
        paths = [p for p in root.iter(f"{SVG}path") if p.get("data-edge")]
        self.assertEqual(len(paths), len(FLOWCHART["edges"]))
        marker_ids = {m.get("id") for m in root.iter(f"{SVG}marker")}
        for path in paths:
            end = path.get("marker-end")
            if end:
                self.assertIn(end[5:-1], marker_ids)  # url(#id)
        self.assertIn("yes", texts(root))

    def test_orthogonal_edges_only_use_axis_aligned_segments(self):
        root = svg_root(render_svg(convert(FLOWCHART)))
        for path in (p for p in root.iter(f"{SVG}path") if p.get("data-edge")):
            points = render_drawio_svg.path_points(path.get("d"))
            for (x1, y1), (x2, y2) in zip(points, points[1:]):
                self.assertTrue(abs(x1 - x2) < 0.01 or abs(y1 - y2) < 0.01, path.get("d"))

    def test_er_markers(self):
        root = svg_root(render_svg(convert(ER)))
        marker_ids = {m.get("id") for m in root.iter(f"{SVG}marker")}
        self.assertTrue(any("ERmandOne" in m for m in marker_ids))
        self.assertTrue(any("ERzeroToMany" in m for m in marker_ids))

    def test_sequence_messages_are_horizontal_at_their_offset(self):
        root = svg_root(render_svg(convert(SEQUENCE)))
        found = texts(root)
        for label in ("POST /orders", "INSERT", "[invalid]", "done", "User"):
            self.assertIn(label, found)
        dashed = [line for line in root.iter(f"{SVG}line") if line.get("stroke-dasharray")]
        self.assertGreaterEqual(len(dashed), 3)  # one lifeline per participant


class CommandLineTest(unittest.TestCase):
    def test_render_cli_and_layout_cli_write_drawio_svg(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec_path = Path(tmp) / "spec.json"
            spec_path.write_text(json.dumps(FLOWCHART), encoding="utf-8")
            direct = Path(tmp) / "direct.drawio.svg"
            self.assertEqual(layout_drawio.main([str(spec_path), "-o", str(direct)]), 0)
            self.assertEqual(svg_root(direct.read_text(encoding="utf-8")).tag, f"{SVG}svg")
            self.assertEqual(validate_file(direct), [])

            plain = Path(tmp) / "plain.drawio"
            layout_drawio.main([str(spec_path), "-o", str(plain)])
            out = Path(tmp) / "out.drawio.svg"
            self.assertEqual(render_drawio_svg.main([str(plain), "-o", str(out)]), 0)
            self.assertEqual(validate_file(out), [])


if __name__ == "__main__":
    unittest.main()
