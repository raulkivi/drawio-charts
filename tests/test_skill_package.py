"""Guards for the skill's documentation and bundled examples."""

import re
import unittest

from helpers import EXAMPLES_DIR, SKILL_DIR

import json

from validate_drawio import validate_file, validate_string

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

    def test_description_claims_mermaid_conversion(self):
        description = frontmatter()["description"].lower()
        self.assertIn("mermaid", description)
        self.assertIn("convert", description)

    def test_skill_md_stays_under_500_lines(self):
        self.assertLess(len(SKILL_MD.read_text(encoding="utf-8").splitlines()), 500)


class ManifestTest(unittest.TestCase):
    def manifests(self):
        root = SKILL_DIR.parent.parent / ".claude-plugin"
        plugin = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads((root / "marketplace.json").read_text(encoding="utf-8"))
        return plugin, marketplace["plugins"][0], marketplace

    def test_versions_agree(self):
        plugin, listing, _ = self.manifests()
        self.assertEqual(plugin["version"], listing["version"])

    def test_descriptions_and_keywords_cover_mermaid_conversion(self):
        plugin, listing, marketplace = self.manifests()
        for description in (plugin["description"], listing["description"], marketplace["description"]):
            self.assertIn("mermaid", description.lower())
        self.assertIn("mermaid", plugin["keywords"])


class LinksTest(unittest.TestCase):
    def test_every_path_mentioned_in_skill_md_exists(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        mentioned = set(re.findall(r"`((?:references|assets|scripts)/[^`\s]+)`", text))
        self.assertIn("assets/examples/mermaid/", mentioned)
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

    def test_script_commands_use_the_skill_dir_path(self):
        # A relative `scripts/...` invites `cd` into the skill directory, which
        # moves the shell away from the user's files (and, sandboxed, loses write
        # access to them). Commands must name the script under <skill-dir>.
        text = SKILL_MD.read_text(encoding="utf-8")
        commands = re.findall(r"`(python3 [^`]+)`", text)
        self.assertTrue(commands)
        relative = [c for c in commands if not c.startswith("python3 <skill-dir>/scripts/")]
        self.assertEqual(relative, [])
        self.assertNotIn("relative to this skill's directory", text)

    def test_no_doc_runs_scripts_by_a_relative_path(self):
        for path in [SKILL_MD, *(SKILL_DIR / "references").glob("*.md")]:
            with self.subTest(doc=path.name):
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"python3 scripts/")

    def test_layout_section_points_to_the_layout_script(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        layout = text[text.index("## Layout"):text.index("## Conventions")]
        self.assertIn("layout_drawio.py", layout)
        self.assertNotIn("There's no auto-layout", layout)

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

    def test_mermaid_examples_convert_cleanly_and_match_their_source(self):
        from graph_spec import GraphSpec, parse_spec
        from layout_drawio import convert
        from replace_mermaid import diagram_type

        folder = EXAMPLES_DIR / "mermaid"
        kinds = set()
        for spec_path in sorted(folder.glob("*.json")):
            with self.subTest(example=spec_path.name):
                mermaid = spec_path.with_suffix(".mmd").read_text(encoding="utf-8")
                spec = parse_spec(json.loads(spec_path.read_text(encoding="utf-8")))
                kinds.add(spec.type)
                self.assertEqual(diagram_type(mermaid), spec.type)
                self.assertEqual(validate_string(convert(spec)), [])
                ids = [n.id for n in spec.nodes] if isinstance(spec, GraphSpec) else [p.id for p in spec.participants]
                for node_id in ids:
                    if not node_id.startswith("_"):   # "_start"/"_end" stand for Mermaid's [*]
                        self.assertIn(node_id, mermaid)
        self.assertEqual(kinds, {"flowchart", "sequence", "er", "class", "state"})

    def test_each_advertised_diagram_type_has_an_example(self):
        names = {p.stem for p in EXAMPLES_DIR.glob("*.drawio")}
        for kind in ("flowchart", "sequence", "er", "org-chart", "network"):
            with self.subTest(kind=kind):
                self.assertTrue(any(re.search(rf"(^|-){kind}(-|$)", name) for name in names), names)


if __name__ == "__main__":
    unittest.main()
