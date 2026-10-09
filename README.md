# draw.io Charts

[![CI](https://github.com/raulkivi/drawio-charts/actions/workflows/validate.yml/badge.svg)](https://github.com/raulkivi/drawio-charts/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A [Claude Code Agent Skill](https://code.claude.com/docs/en/skills) that teaches Claude how to generate and edit [draw.io](https://www.drawio.com/) (`diagrams.net`) diagrams — as plain XML, with no draw.io application required. Works in the Claude Code CLI and the Claude Code VS Code extension.

Ask for a flowchart, system/network architecture diagram, org chart, ER diagram, or sequence diagram, and it produces a valid `.drawio` file: correct `mxfile`/`mxGraphModel`/`mxCell` structure, consistent styling, and unique, well-formed ids and connections — the kind of detail that's easy to get subtly wrong when generating this XML from scratch.

```
> create a .drawio flowchart for a password reset flow: request → email sent → link
  clicked → new password → confirmation
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
├── SKILL.md                          # Entry point: workflow, skeleton, style cheatsheet, conventions
├── references/                       # Loaded on demand for full API/format detail
│   ├── format-reference.md           # mxfile / mxGraphModel / mxCell XML structure
│   ├── style-reference.md            # Full style property tables
│   ├── mxcell-api-reference.md       # mxCell JS API (for scripted generation)
│   └── mxgeometry-api-reference.md   # mxGeometry JS API: positioning, waypoints
└── assets/examples/
    └── company-network.drawio        # Worked example diagram
.claude/skills/drawio-charts          # Symlink to skills/drawio-charts, so opening this
                                       # repo directly in Claude Code also auto-loads the skill
```

`SKILL.md` is the always-loaded summary; the `references/` docs are pulled in only when a task needs that level of detail, so the skill stays cheap to keep loaded (see [Anthropic's progressive-disclosure guidance](https://code.claude.com/docs/en/skills)).

## Previewing the result

Install the **Draw.io Integration** VS Code extension (`hediet.vscode-drawio`) to open generated `.drawio` files in a visual editor.

## Contributing

Issues and PRs welcome — especially additional worked examples under `skills/drawio-charts/assets/examples/` or gaps found in the style/format references. `.github/workflows/validate.yml` runs `claude plugin validate --strict` on the plugin and marketplace manifests (run it locally with `claude plugin validate --strict .` before opening a PR), checks that `SKILL.md` has the required frontmatter, and example `.drawio` files are well-formed XML.

## License

[MIT](LICENSE)
