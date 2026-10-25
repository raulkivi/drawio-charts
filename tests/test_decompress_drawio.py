import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from helpers import compress, drawio, graph_model, vertex

import decompress_drawio
from validate_drawio import validate_string


class DecompressTest(unittest.TestCase):
    def test_compressed_page_becomes_plain_xml(self):
        packed = f'<mxfile><diagram id="p" name="P">{compress(graph_model(vertex("a")))}</diagram></mxfile>'
        plain = decompress_drawio.decompress_string(packed)
        diagram = ET.fromstring(plain).find("diagram")
        self.assertIsNotNone(diagram.find("mxGraphModel"))
        self.assertEqual((diagram.text or "").strip(), "")
        self.assertEqual(diagram.get("name"), "P")
        self.assertEqual(validate_string(plain), [])

    def test_every_compressed_page_is_decoded_and_plain_pages_are_kept(self):
        packed = (
            "<mxfile>"
            f'<diagram id="p1" name="Overview">{compress(graph_model(vertex("a")))}</diagram>'
            f'<diagram id="p2" name="Plain">{graph_model(vertex("b"))}</diagram>'
            f'<diagram id="p3" name="Deployment">{compress(graph_model(vertex("c")))}</diagram>'
            "</mxfile>"
        )
        root = ET.fromstring(decompress_drawio.decompress_string(packed))
        pages = root.findall("diagram")
        self.assertEqual([p.get("name") for p in pages], ["Overview", "Plain", "Deployment"])
        for page, cell_id in zip(pages, "abc"):
            self.assertEqual((page.text or "").strip(), "")
            self.assertIsNotNone(page.find(f"mxGraphModel/root/mxCell[@id='{cell_id}']"))

    def test_plain_file_is_left_equivalent(self):
        plain = drawio(vertex("a"))
        result = decompress_drawio.decompress_string(plain)
        self.assertEqual(ET.fromstring(result).find("diagram/mxGraphModel/root/mxCell[@id='a']").get("vertex"), "1")

    def test_main_writes_output_file(self):
        packed = f'<mxfile><diagram id="p" name="P">{compress(graph_model(vertex("a")))}</diagram></mxfile>'
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "in.drawio", Path(tmp) / "out.drawio"
            src.write_text(packed, encoding="utf-8")
            self.assertEqual(decompress_drawio.main([str(src), "-o", str(dst)]), 0)
            self.assertIn("<mxGraphModel", dst.read_text(encoding="utf-8"))

    def test_main_in_place(self):
        packed = f'<mxfile><diagram id="p" name="P">{compress(graph_model(vertex("a")))}</diagram></mxfile>'
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.drawio"
            src.write_text(packed, encoding="utf-8")
            self.assertEqual(decompress_drawio.main([str(src), "--in-place"]), 0)
            self.assertIn("<mxGraphModel", src.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
