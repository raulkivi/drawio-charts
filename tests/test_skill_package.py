"""Guards for the skill's documentation and bundled examples."""

import re
import unittest

from helpers import EXAMPLES_DIR, SKILL_DIR

from validate_drawio import validate_file

SKILL_MD = SKILL_DIR / "SKILL.md"


def frontmatter() -> dict:
    text = SKILL_MD.read_text(encoding="utf-8")
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    block = text[4:text.index("\n---", 4)]
    return dict(line.split(":", 1) for line in block.splitlines() if ":" in line)


class FrontmatterTest(unittest.TestCase):
    def test_has_name_and_description(self):
        fields = frontmatter()
        self.assertEqual(fields["name"].strip(), "drawio-charts")
        self.assertTrue(fields["description"].strip())

    def test_description_excludes_data_charts(self):
        description = frontmatter()["description"].lower()
        self.assertIn("not for data", description)

    def test_skill_md_stays_under_500_lines(self):
        self.assertLess(len(SKILL_MD.read_text(encoding="utf-8").splitlines()), 500)


class LinksTest(unittest.TestCase):
    def test_every_path_mentioned_in_skill_md_exists(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        mentioned = set(re.findall(r"`((?:references|assets|scripts)/[^`\s]+)`", text))
        self.assertTrue(mentioned)
        missing = [path for path in mentioned if not any(SKILL_DIR.glob(path))]
        self.assertEqual(missing, [])

    def test_every_bundled_file_is_mentioned_in_skill_md(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        bundled = [
            p.relative_to(SKILL_DIR).as_posix()
            for folder in ("references", "assets/examples", "scripts")
            for p in (SKILL_DIR / folder).glob("*")
            if p.is_file() and p.suffix in {".md", ".drawio", ".py"}
        ]
        unmentioned = [path for path in bundled if path not in text]
        self.assertEqual(unmentioned, [])

    def test_long_references_have_a_table_of_contents(self):
        for path in (SKILL_DIR / "references").glob("*.md"):
            text = path.read_text(encoding="utf-8")
            if len(text.splitlines()) > 300:
                self.assertTrue("## Contents" in text, f"{path.name} needs a '## Contents' section")


class ExamplesTest(unittest.TestCase):
    def test_examples_validate_cleanly(self):
        examples = sorted(EXAMPLES_DIR.glob("*.drawio"))
        self.assertTrue(examples)
        for path in examples:
            with self.subTest(example=path.name):
                self.assertEqual(validate_file(path), [])

    def test_each_advertised_diagram_type_has_an_example(self):
        names = {p.stem for p in EXAMPLES_DIR.glob("*.drawio")}
        for kind in ("flowchart", "sequence", "er", "org-chart", "network"):
            with self.subTest(kind=kind):
                self.assertTrue(any(re.search(rf"(^|-){kind}(-|$)", name) for name in names), names)


if __name__ == "__main__":
    unittest.main()
