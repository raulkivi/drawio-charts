# draw.io Charts

[![CI](https://github.com/raulkivi/drawio-charts/actions/workflows/validate.yml/badge.svg)](https://github.com/raulkivi/drawio-charts/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A [Claude Code Agent Skill](https://code.claude.com/docs/en/skills) that teaches Claude how to generate and edit [draw.io](https://www.drawio.com/) (`diagrams.net`) diagrams — as plain XML, with no draw.io application required. Works in the Claude Code CLI and the Claude Code VS Code extension.

Ask for a flowchart, system/network architecture diagram, org chart, ER diagram, or sequence diagram, and it produces a valid `.drawio` file: correct `mxfile`/`mxGraphModel`/`mxCell` structure, consistent styling, and unique, well-formed ids and connections — the kind of detail that's easy to get subtly wrong when generating this XML from scratch. A bundled validator script checks each diagram before it's handed back, and compressed `.drawio` files are decoded so they can be edited.

It also **converts Mermaid diagrams** (flowchart, sequence, class, state, ER) into editable draw.io diagrams, and can replace the ```` ```mermaid ```` blocks in your Markdown docs with `.drawio.svg` images. Those display inline on GitHub/GitLab and open as editable diagrams in draw.io or the VS Code draw.io extension. The original Mermaid is kept in a comment, so the change can be undone. No draw.io installation is needed: the bundled scripts do the layout and draw the SVG.

It's for editable diagrams, not data charts (bar/line/pie plots).

```
> create a .drawio flowchart for a password reset flow: request → email sent → link
  clicked → new password → confirmation

> convert the mermaid diagrams in docs/ to draw.io and replace them in the markdown
```

## Install

**Option A — as a plugin (recommended):**

```
/plugin marketplace add raulkivi/drawio-charts
/plugin install drawio-charts@drawio-charts
```

**Option B — copy directly into a project:**

Copy [`skills/drawio-charts/`](skills/drawio-charts/) into that project's `.claude/skills/` (or into `~/.claude/skills/` to make it available everywhere). No build step, no dependencies.

## Structure

```
.claude-plugin/
├── plugin.json                       # Plugin manifest
└── marketplace.json                  # Marketplace listing (so `/plugin marketplace add` works)
skills/drawio-charts/
├── SKILL.md                          # Entry point: workflow, layout rules, skeleton, styles, checklist
├── scripts/                          # Python 3 standard library only
│   ├── validate_drawio.py            # Structural validator (ids, parents, edges, geometry, styles)
│   ├── decompress_drawio.py          # Compressed <diagram> pages -> plain editable XML
│   ├── layout_drawio.py              # Graph spec (from Mermaid) -> laid-out .drawio / .drawio.svg
│   ├── render_drawio_svg.py          # .drawio -> editable .drawio.svg, no draw.io app needed
│   ├── replace_mermaid.py            # Plan / apply / restore Mermaid -> image swaps in Markdown
│   └── graph_spec.py, layered_layout.py, graph_render.py, sequence_render.py,
│       edge_router.py, drawio_writer.py, text_metrics.py, drawio_io.py   # their building blocks
├── references/                       # Loaded on demand
│   ├── format-reference.md           # XML structure: pages, cells, parents, geometry, UserObject, compression
│   ├── style-reference.md            # Full style property tables
│   └── mermaid-mapping.md            # Mermaid -> graph spec translation guide
├── assets/examples/                  # One worked example per diagram type
│   ├── password-reset-flowchart.drawio
│   ├── checkout-sequence.drawio
│   ├── blog-er-diagram.drawio
│   ├── engineering-org-chart.drawio
│   ├── company-network.drawio
│   └── mermaid/                      # Mermaid source + graph spec pairs for each supported type
└── evals/                            # Test prompts + graders (`claude plugin eval` layout)
tests/                                # unittest suite for the scripts, docs and examples
.claude/skills/drawio-charts          # Symlink to skills/drawio-charts, so opening this
                                       # repo directly in Claude Code also auto-loads the skill
```

`SKILL.md` is the always-loaded summary; the `references/` docs are pulled in only when a task needs that level of detail, so the skill stays cheap to keep loaded (see [Anthropic's progressive-disclosure guidance](https://code.claude.com/docs/en/skills)).

## Previewing the result

Install the **Draw.io Integration** VS Code extension (`hediet.vscode-drawio`) to open generated `.drawio` files in a visual editor.

## Contributing

Issues and PRs welcome — especially additional worked examples under `skills/drawio-charts/assets/examples/` or gaps found in the style/format references.

Run the checks locally before opening a PR:

```bash
python3 -m unittest discover -s tests                                   # scripts, SKILL.md links/frontmatter, examples
python3 skills/drawio-charts/scripts/validate_drawio.py path/to/file.drawio
claude plugin validate --strict .                                       # plugin + marketplace manifests
claude plugin eval skills/drawio-charts --allow-tools Write,Edit,Bash --scaffold   # optional: billed model runs
```

New behaviour in the scripts starts with a failing test in `tests/`. New examples are picked up automatically by the test that validates every file in `assets/examples/`. `.github/workflows/validate.yml` runs the unit tests, the validator on the examples, and `claude plugin validate --strict`.

## License

[MIT](LICENSE).

The files in `skills/drawio-charts/references/` summarise the [mxGraph](https://github.com/jgraph/mxgraph) API documentation, which is licensed under [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0). Copyright the respective mxGraph / JGraph authors. This project is not affiliated with or endorsed by draw.io or JGraph.
