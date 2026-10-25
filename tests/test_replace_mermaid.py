import io
import json
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from helpers import SCRIPTS_DIR  # noqa: F401

import replace_mermaid
from replace_mermaid import apply_plan, diagram_type, find_blocks, plan_files, restore_text

DOC = textwrap.dedent("""\
    # Orders

    Intro text with `inline` code.

    ```mermaid
    flowchart TD
      A[Order] --> B{Paid?}
      B -->|yes| C[Ship]
    ```

    ## Checkout

    ~~~mermaid
    sequenceDiagram
      U->>API: POST
    ~~~

    ```python
    print("not mermaid")
    ```

    ````markdown
    ```mermaid
    graph LR
      X --> Y
    ```
    ````

    - A list item:

      ```mermaid
      ---
      title: Order states
      ---
      stateDiagram-v2
        [*] --> Open
      ```

    ```mermaid
    gantt
      title Plan
    ```
    """)


class FindBlocksTest(unittest.TestCase):
    def test_finds_only_real_mermaid_fences(self):
        blocks = find_blocks(DOC)
        self.assertEqual([b.kind for b in blocks], ["flowchart", "sequence", "state", "gantt"])
        self.assertEqual(blocks[0].code, "flowchart TD\n  A[Order] --> B{Paid?}\n  B -->|yes| C[Ship]\n")
        self.assertEqual(blocks[2].indent, "  ")
        self.assertEqual(blocks[2].code.splitlines()[0], "---")

    def test_supported_flag(self):
        self.assertEqual([b.supported for b in find_blocks(DOC)], [True, True, True, False])

    def test_titles_from_front_matter_then_heading(self):
        blocks = find_blocks(DOC)
        self.assertEqual([b.title for b in blocks], ["Orders", "Checkout", "Order states", "Checkout"])

    def test_diagram_type_detection(self):
        cases = {
            "graph LR\nA-->B": "flowchart", "flowchart TB\nA-->B": "flowchart",
            "%%{init: {'theme': 'dark'}}%%\nsequenceDiagram\nA->>B: hi": "sequence",
            "%% a comment\nerDiagram\nA ||--o{ B : has": "er", "classDiagram\nA <|-- B": "class",
            "stateDiagram\n[*] --> A": "state", "---\ntitle: x\n---\nclassDiagram\nA": "class",
            "pie\n\"a\": 1": "pie", "": "unknown",
        }
        for code, kind in cases.items():
            with self.subTest(code=code):
                self.assertEqual(diagram_type(code), kind)


class PlanAndApplyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.doc = self.root / "docs" / "orders.md"
        self.doc.parent.mkdir()
        self.doc.write_text(DOC, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def make_images(self, plan):
        for entry in plan:
            if entry["supported"]:
                image = self.doc.parent / entry["image"]
                image.parent.mkdir(exist_ok=True)
                image.write_text("<svg/>", encoding="utf-8")

    def test_plan_suggests_unique_images_next_to_the_file(self):
        plan = plan_files([self.root])
        self.assertEqual([e["image"] for e in plan], [
            "diagrams/orders.drawio.svg", "diagrams/checkout.drawio.svg",
            "diagrams/order-states.drawio.svg", "diagrams/checkout-2.drawio.svg",
        ])
        self.assertEqual(plan[0]["file"], str(self.doc))
        self.assertEqual(plan[0]["line"], 5)

    def test_apply_replaces_blocks_and_keeps_source_in_a_comment(self):
        plan = plan_files([self.root])
        self.make_images(plan)
        report = apply_plan(plan)
        self.assertEqual(report["replaced"], 3)
        self.assertEqual(report["skipped"], [{"file": str(self.doc), "index": 3, "reason": "unsupported type gantt"}])
        text = self.doc.read_text(encoding="utf-8")
        self.assertIn("![Orders](diagrams/orders.drawio.svg)", text)
        self.assertIn("  ![Order states](diagrams/order-states.drawio.svg)", text)  # list indentation kept
        self.assertIn("<!-- mermaid-source: diagrams/orders.drawio.svg", text)
        self.assertEqual([b.kind for b in find_blocks(text)], ["gantt"])
        self.assertIn('print("not mermaid")', text)
        self.assertIn("````markdown\n```mermaid\ngraph LR", text)

    def test_comment_cannot_be_closed_early_by_mermaid_arrows(self):
        plan = plan_files([self.root])
        self.make_images(plan)
        apply_plan(plan)
        text = self.doc.read_text(encoding="utf-8")
        comments = text.split("<!-- mermaid-source")[1:]
        self.assertEqual(len(comments), 3)
        for comment in comments:
            # the first "-->" must be the comment's own end, right after the closing fence
            before_end = comment[:comment.index("-->")]
            self.assertTrue(before_end.rstrip().endswith(("```", "~~~")), before_end)

    def test_apply_is_idempotent_and_skips_missing_images(self):
        plan = plan_files([self.root])
        image = self.doc.parent / plan[0]["image"]
        image.parent.mkdir()
        image.write_text("<svg/>", encoding="utf-8")
        report = apply_plan(plan)
        self.assertEqual(report["replaced"], 1)
        reasons = {s["index"]: s["reason"] for s in report["skipped"]}
        self.assertEqual(reasons[1], "image diagrams/checkout.drawio.svg does not exist")
        once = self.doc.read_text(encoding="utf-8")
        report = apply_plan(plan)
        self.assertEqual(report["replaced"], 0)
        self.assertEqual(self.doc.read_text(encoding="utf-8"), once)

    def test_stale_plan_entries_are_skipped(self):
        plan = plan_files([self.root])
        self.make_images(plan)
        self.doc.write_text(DOC.replace("B -->|yes| C[Ship]", "B -->|yes| D[Deliver]"), encoding="utf-8")
        report = apply_plan(plan)
        reasons = {s["index"]: s["reason"] for s in report["skipped"]}
        self.assertIn("changed since", reasons[0])

    def test_restore_round_trips_exactly(self):
        plan = plan_files([self.root])
        self.make_images(plan)
        apply_plan(plan)
        self.assertEqual(restore_text(self.doc.read_text(encoding="utf-8")), DOC)

    def test_escaping_is_reversible_for_awkward_text(self):
        for line in ("A --> B", "A ---> B", "literal --&gt; text", "--&amp;", "x --!> y", "plain"):
            with self.subTest(line=line):
                escaped = replace_mermaid._escape(line)
                self.assertNotIn("-->", escaped)
                self.assertEqual(replace_mermaid._unescape(escaped), line)

    def test_crlf_files_round_trip(self):
        crlf = DOC.replace("\n", "\r\n")
        self.doc.write_bytes(crlf.encode())
        plan = plan_files([self.root])
        self.make_images(plan)
        apply_plan(plan)
        converted = self.doc.read_bytes().decode()
        self.assertNotIn("\n", converted.replace("\r\n", ""))  # no bare LF introduced
        self.assertEqual(restore_text(converted), crlf)

    def test_command_line(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(replace_mermaid.main(["list", str(self.root), "--json"]), 0)
        plan = json.loads(out.getvalue())
        self.make_images(plan)
        plan_path = self.root / "plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(replace_mermaid.main(["apply", str(plan_path)]), 0)
        self.assertIn("replaced 3", out.getvalue())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(replace_mermaid.main(["restore", str(self.doc)]), 0)
        self.assertEqual(self.doc.read_text(encoding="utf-8"), DOC)


if __name__ == "__main__":
    unittest.main()
