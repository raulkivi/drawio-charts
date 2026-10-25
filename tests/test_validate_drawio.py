import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from helpers import compress, drawio, edge, graph_model, vertex

import validate_drawio
from validate_drawio import validate_string


def messages(issues):
    return [issue.message for issue in issues]


class ValidDiagramsTest(unittest.TestCase):
    def test_minimal_diagram_has_no_issues(self):
        xml = drawio(vertex("a") + vertex("b") + edge("e1", "a", "b"))
        self.assertEqual(validate_string(xml), [])

    def test_container_children_may_use_the_container_as_parent(self):
        xml = drawio(
            vertex("vpc", style="swimlane;container=1;")
            + vertex("web", parent="vpc")
            + vertex("db", parent="vpc")
            + edge("e1", "web", "db", parent="vpc")
        )
        self.assertEqual(validate_string(xml), [])

    def test_edge_label_child_of_edge_needs_no_size(self):
        label = vertex(
            "lbl", parent="e1", style="edgeLabel;html=1;",
            geometry='<mxGeometry x="-0.2" relative="1" as="geometry"><mxPoint as="offset"/></mxGeometry>',
        )
        xml = drawio(vertex("a") + vertex("b") + edge("e1", "a", "b") + label)
        self.assertEqual(validate_string(xml), [])

    def test_edge_may_connect_to_another_edge(self):
        xml = drawio(vertex("a") + vertex("b") + vertex("c") + edge("e1", "a", "b") + edge("e2", "c", "e1"))
        self.assertEqual(validate_string(xml), [])

    def test_edge_with_terminal_points_instead_of_cells_is_valid(self):
        geometry = (
            '<mxGeometry relative="1" as="geometry">'
            '<mxPoint x="10" y="10" as="sourcePoint"/><mxPoint x="90" y="10" as="targetPoint"/>'
            "</mxGeometry>"
        )
        xml = drawio(edge("line", None, None, geometry=geometry))
        self.assertEqual(validate_string(xml), [])

    def test_extra_layers_are_valid_parents(self):
        root_cells = '<mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="notes" value="Notes" parent="0"/>'
        xml = drawio(vertex("a") + vertex("n1", parent="notes"), root_cells=root_cells)
        self.assertEqual(validate_string(xml), [])

    def test_user_object_wrapper_carries_the_id(self):
        wrapped = (
            '<UserObject label="API" owner="team-a" id="api">'
            '<mxCell style="rounded=1;" parent="1" vertex="1">'
            '<mxGeometry x="0" y="0" width="120" height="60" as="geometry"/></mxCell></UserObject>'
        )
        xml = drawio(vertex("a") + wrapped + edge("e1", "a", "api"))
        self.assertEqual(validate_string(xml), [])

    def test_named_style_tokens_and_data_uri_images_are_valid(self):
        style = "image;html=1;image=data:image/svg+xml,PHN2Zz4=;aspect=fixed;"
        xml = drawio(vertex("img", style=style) + vertex("t", style="text;html=1;"))
        self.assertEqual(validate_string(xml), [])

    def test_bare_graph_model_root_is_accepted(self):
        xml = graph_model(vertex("a"))
        self.assertEqual(validate_string(xml), [])

    def test_ids_may_repeat_on_different_pages(self):
        page = graph_model(vertex("a"))
        xml = f'<mxfile><diagram id="p1" name="One">{page}</diagram><diagram id="p2" name="Two">{page}</diagram></mxfile>'
        self.assertEqual(validate_string(xml), [])

    def test_compressed_diagram_is_decoded_and_validated(self):
        xml = f'<mxfile><diagram id="p1" name="Packed">{compress(graph_model(vertex("a")))}</diagram></mxfile>'
        self.assertEqual(validate_string(xml), [])


class InvalidDiagramsTest(unittest.TestCase):
    def assertSingleIssue(self, xml, *fragments):
        issues = validate_string(xml)
        self.assertEqual(len(issues), 1, messages(issues))
        for fragment in fragments:
            self.assertIn(fragment, issues[0].message)
        return issues[0]

    def test_malformed_xml(self):
        self.assertSingleIssue("<mxfile><diagram>", "well-formed")

    def test_file_without_any_diagram(self):
        self.assertSingleIssue("<mxfile></mxfile>", "no <diagram>")

    def test_duplicate_ids(self):
        issue = self.assertSingleIssue(drawio(vertex("a") + vertex("a")), "duplicate id")
        self.assertEqual(issue.cell_id, "a")

    def test_duplicate_page_ids(self):
        page = graph_model(vertex("a"))
        xml = f'<mxfile><diagram id="p" name="One">{page}</diagram><diagram id="p" name="Two">{page}</diagram></mxfile>'
        self.assertSingleIssue(xml, "duplicate diagram id")

    def test_missing_root_cell(self):
        self.assertSingleIssue(drawio(vertex("a", parent="1"), root_cells='<mxCell id="1"/>'), 'root cell "0"')

    def test_missing_layer(self):
        self.assertSingleIssue(drawio("", root_cells='<mxCell id="0"/>'), "layer")

    def test_parent_must_exist(self):
        self.assertSingleIssue(drawio(vertex("a", parent="ghost")), 'parent "ghost"')

    def test_cell_must_not_be_its_own_parent(self):
        self.assertSingleIssue(drawio(vertex("a", parent="a")), "own parent")

    def test_cell_must_be_vertex_or_edge(self):
        cell = '<mxCell id="x" parent="1"><mxGeometry width="10" height="10" as="geometry"/></mxCell>'
        self.assertSingleIssue(drawio(cell), 'vertex="1" or edge="1"')

    def test_cell_cannot_be_both_vertex_and_edge(self):
        cell = '<mxCell id="x" parent="1" vertex="1" edge="1"><mxGeometry width="10" height="10" as="geometry"/></mxCell>'
        self.assertSingleIssue(drawio(cell), "both")

    def test_edge_target_must_exist(self):
        issue = self.assertSingleIssue(drawio(vertex("a") + edge("e1", "a", "nope")), 'target "nope"')
        self.assertEqual(issue.cell_id, "e1")

    def test_edge_cannot_attach_to_a_layer(self):
        self.assertSingleIssue(drawio(vertex("a") + edge("e1", "a", "1")), "layer")

    def test_dangling_edge_without_terminal_point(self):
        self.assertSingleIssue(drawio(vertex("a") + edge("e1", "a", None)), "no target")

    def test_vertex_needs_geometry(self):
        cell = '<mxCell id="a" parent="1" vertex="1"/>'
        self.assertSingleIssue(drawio(cell), "geometry")

    def test_vertex_needs_width_and_height(self):
        cell = vertex("a", geometry='<mxGeometry x="0" y="0" width="120" as="geometry"/>')
        self.assertSingleIssue(drawio(cell), "height")

    def test_vertex_size_must_be_numeric(self):
        cell = vertex("a", geometry='<mxGeometry x="0" y="0" width="wide" height="60" as="geometry"/>')
        self.assertSingleIssue(drawio(cell), "width")

    def test_edge_needs_geometry(self):
        cell = '<mxCell id="e1" parent="1" source="a" target="b" edge="1"/>'
        self.assertSingleIssue(drawio(vertex("a") + vertex("b") + cell), "geometry")

    def test_style_missing_semicolon(self):
        cell = vertex("a", style="rounded=1fillColor=#dae8fc;")
        self.assertSingleIssue(drawio(cell), "missing ';'")

    def test_issues_name_the_page(self):
        issue = self.assertSingleIssue(drawio(vertex("a", parent="ghost"), name="Overview"), "ghost")
        self.assertEqual(issue.diagram, "Overview")

    def test_corrupt_compressed_diagram(self):
        self.assertSingleIssue('<mxfile><diagram id="p" name="P">not-base64!!</diagram></mxfile>', "decode")


class CommandLineTest(unittest.TestCase):
    def run_cli(self, *contents):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for index, content in enumerate(contents):
                path = Path(tmp) / f"d{index}.drawio"
                path.write_text(content, encoding="utf-8")
                paths.append(str(path))
            out = io.StringIO()
            with redirect_stdout(out):
                code = validate_drawio.main(paths)
            return code, out.getvalue()

    def test_valid_file_exits_zero(self):
        code, output = self.run_cli(drawio(vertex("a")))
        self.assertEqual(code, 0)
        self.assertIn("OK", output)

    def test_invalid_file_exits_one_and_reports(self):
        code, output = self.run_cli(drawio(vertex("a")), drawio(vertex("a", parent="ghost")))
        self.assertEqual(code, 1)
        self.assertIn("d1.drawio", output)
        self.assertIn("ghost", output)

    def test_missing_file_is_reported(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = validate_drawio.main(["/nonexistent/x.drawio"])
        self.assertEqual(code, 1)
        self.assertIn("cannot read", out.getvalue())


if __name__ == "__main__":
    unittest.main()
