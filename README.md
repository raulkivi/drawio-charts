# draw.io Charts Skill

An [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills) that teaches Claude (in Claude Code, the VS Code extension, or any other Claude Code-compatible surface) how to generate and edit [draw.io](https://www.drawio.com/) (`diagrams.net`) diagrams — directly as XML, with no draw.io application required.

## What it does

Point Claude at this skill and ask for a flowchart, architecture diagram, network diagram, org chart, ER diagram, or sequence diagram, and it will produce a valid `.drawio` file: correct `mxfile`/`mxGraphModel`/`mxCell` structure, consistent styling, and unique/well-formed ids and connections.

## Structure

```
.claude/skills/drawio-charts/
├── SKILL.md                          # Entry point: workflow, skeleton, style cheatsheet, conventions
├── references/                       # Loaded on demand for the full API/format detail
│   ├── format-reference.md           # mxfile / mxGraphModel / mxCell XML structure
│   ├── style-reference.md            # Full style property tables
│   ├── mxcell-api-reference.md       # mxCell JS API (for scripted generation)
│   └── mxgeometry-api-reference.md   # mxGeometry JS API: positioning, waypoints
└── assets/examples/
    └── company-network.drawio        # Worked example diagram
```

`SKILL.md` is the always-loaded summary; the `references/` docs are pulled in only when a task needs that level of detail (progressive disclosure keeps the skill cheap to keep loaded).

## Using it

- **Claude Code / VS Code extension**: open this repository (or copy `.claude/skills/drawio-charts/` into another project's `.claude/skills/`) — the skill is discovered automatically and activates when you ask for a draw.io diagram.
- **Previewing a result**: install the **Draw.io Integration** VS Code extension (`hediet.vscode-drawio`) to open `.drawio` files in a visual editor.

## Scratch space

`diagrams/` (gitignored) is a convenient default location for diagrams you ask Claude to create while working in this repo — point it elsewhere if you'd rather organize by project.
