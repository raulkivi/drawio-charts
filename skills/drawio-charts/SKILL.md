---
name: drawio-charts
description: Create, edit, and validate draw.io (diagrams.net) .drawio XML diagrams — flowcharts, system/network/cloud architecture diagrams, org charts, sequence diagrams, ER/database schema diagrams. Use whenever the user asks to create or modify a draw.io or diagrams.net file, a .drawio/.dio file, or wants an architecture, process, workflow, network, schema or hierarchy drawn as an editable diagram, even if they don't say "draw.io". Not for data charts (bar, line, pie, scatter plots of numbers) or Mermaid/PlantUML text diagrams unless the user wants them as a .drawio file.
---

# draw.io Chart Creation

Generate and edit `.drawio` files directly as XML — no draw.io application is required to produce a valid diagram. The XML format (`mxfile` / `mxGraphModel` / `mxCell`) is documented in full under `references/`; this file covers what's needed for the common case.

## Workflow

1. Work out the diagram type and the entities and relationships to show. Ask only if the content is unclear; infer the type from the request.
2. Open the matching example from the table under "Diagram types" and copy its patterns. Each one encodes the shapes, styles and nesting that type needs.
3. Work out rows, columns and coordinates before writing any cells (see "Layout"), then write the XML from the skeleton below: one `mxCell` per shape and one per connector.
4. Style consistently: the same kind of element gets the same shape and palette entry.
5. Run `python3 <skill-dir>/scripts/validate_drawio.py <file>` and fix every issue it reports. It checks ids, parents, edge endpoints, geometry and style separators, which are the mistakes that make draw.io drop cells or refuse to open the file. Then read through the Validation checklist for what a script can't judge.
6. Mention that the user can open the file in draw.io or the `hediet.vscode-drawio` VS Code extension to see it. Don't depend on that to verify correctness.

**Running the scripts.** `<skill-dir>` is the directory this SKILL.md is in. Run the scripts from the user's working directory, giving the script's full path and the diagram's usual path. Don't `cd` into the skill directory: the shell's working directory carries over to later commands, so relative paths then point at the wrong place, and in a sandboxed session only the original working directory may be writable.

### Editing an existing file

1. Check whether each `<diagram>` holds an `<mxGraphModel>` or a block of base64-looking text. Text means the page is compressed. Run `python3 <skill-dir>/scripts/decompress_drawio.py <file> --in-place`, which decodes every compressed page and keeps the others as they are. Use the script rather than decoding by hand: draw.io's encoding is deflate plus URL-encoding, so a hand decode is easy to get subtly wrong. draw.io opens the plain form just as well.
2. A file can have several pages. Apply the change to each page it concerns ("on both pages", or a component that appears on several), and leave the other pages alone.
3. Keep existing ids, labels and styles. Move existing shapes only to make room, and say which ones you moved.
4. "Put X between A and B" means reroute: replace the A→B edge with A→X and X→B, unless the user says A should still reach B directly. If X belongs in a container that A and B are in, give it that container's id as `parent` and container-relative coordinates.
5. Validate the edited file, as for a new one.

## Minimal file skeleton

```xml
<mxfile host="app.diagrams.net" agent="draw.io" version="21.0.0">
  <diagram id="unique-diagram-id" name="Diagram Name">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1100" pageHeight="850">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- shapes and connectors go here, parent="1" -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

A file can contain multiple `<diagram>` elements for a multi-page document; each needs its own unique `id`.

## Shapes (vertices) and connectors (edges)

```xml
<!-- Shape -->
<mxCell id="node1" value="Label Text"
        style="rounded=1;fillColor=#dae8fc;strokeColor=#6c8ebf;whiteSpace=wrap;html=1;"
        parent="1" vertex="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
</mxCell>

<!-- Connector -->
<mxCell id="edge1" value=""
        style="endArrow=classic;edgeStyle=orthogonalEdgeStyle;strokeColor=#666666;"
        parent="1" source="node1" target="node2" edge="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

Required attributes: every cell needs a unique `id` and a `parent` that exists. Shapes need `vertex="1"` plus an `mxGeometry` with `x`/`y`/`width`/`height`. Connectors need `edge="1"`, `source`/`target` ids of existing cells, and a `relative="1"` geometry (add waypoints via a nested `<Array as="points"><mxPoint .../></Array>` if needed).

**Parents.** Top-level cells use `parent="1"` (the default layer). Cells inside a container, swimlane, group or ER table use the container's id as `parent`, and their `x`/`y` are relative to the container's top-left corner, not the page. A label floating on a connector is a vertex whose `parent` is the edge. `references/format-reference.md` covers layers, containers, edge labels, relative geometry and custom properties.

## Style cheatsheet

```
# Fill / stroke
fillColor=#dae8fc;strokeColor=#6c8ebf;strokeWidth=2;rounded=1;dashed=1;opacity=80

# Text
fontColor=#333333;fontSize=12;fontStyle=1;align=center;verticalAlign=middle;whiteSpace=wrap;html=1

# Edges
endArrow=classic;startArrow=none;edgeStyle=orthogonalEdgeStyle;curved=1

# Basic shapes
shape=rectangle | ellipse | rhombus | triangle | hexagon | cylinder | actor | cloud | document
```

Full property tables (containers, image shapes, arrow types, font-style bitmask, gradients, ER arrowheads, etc.) are in `references/style-reference.md`.

### Recommended color palette

| Purpose | Fill | Stroke |
|---|---|---|
| Default/Neutral | `#f5f5f5` | `#666666` |
| Primary/Info | `#dae8fc` | `#6c8ebf` |
| Success/Start | `#d5e8d4` | `#82b366` |
| Warning | `#fff2cc` | `#d6b656` |
| Error/End | `#f8cecc` | `#b85450` |
| Purple/Special | `#e1d5e7` | `#9673a6` |

### Image/stencil shapes (network & cloud diagrams)

Reference bundled draw.io shape libraries by path — no need to embed image data:

```
image=img/lib/active_directory/{laptop_client,domain_controller,database_server,generic_server,switch,router,firewall,internet_cloud,workstation_client,web_server,cluster_server}.svg
image=img/lib/mscae/{Active_Directory,SQL_Database_generic,Virtual_Machine,Virtual_Network,Monitor,Client_Apps,Storage,Kubernetes_Services}.svg
shape=mxgraph.computers.{laptop,server} | mxgraph.cisco.switches.workgroup_switch
```

Typical image-shape style string:

```
image;aspect=fixed;perimeter=ellipsePerimeter;html=1;align=center;image=img/lib/active_directory/[shape].svg;labelPosition=center;verticalLabelPosition=bottom;verticalAlign=top;fontSize=11;
```

See `assets/examples/company-network.drawio` for a complete worked example (internet → router → switch → domain controller / file server / 5 workstations) using this pattern.

## Diagram types

| Type | Example to copy | Key patterns |
|---|---|---|
| Flowchart / process | `assets/examples/password-reset-flowchart.drawio` | `ellipse` start/end, `rhombus` decisions, Yes/No edge labels, waypoint for a loop-back |
| Sequence | `assets/examples/checkout-sequence.drawio` | `shape=umlLifeline` containers, activation bars as their children, messages placed with `exitDy`/`entryDy`, dashed replies |
| ER / database schema | `assets/examples/blog-er-diagram.drawio` | swimlane tables with one `text` row per column, edges from FK row to PK row, `ERmandOne` / `ERzeroToMany` ends |
| Org chart / hierarchy | `assets/examples/engineering-org-chart.drawio` | top-down tree, HTML labels (name + title), `exitX=0.5;exitY=1;entryX=0.5;entryY=0` elbows, a department container |
| Network / infrastructure | `assets/examples/company-network.drawio` | `image=img/lib/...` stencil shapes with labels below |
| Cloud / system architecture | `company-network` for stencils, `engineering-org-chart` for containers | Group services in containers (VPC, subnet, cluster) |

## Layout

There's no auto-layout when you write XML, so place every shape deliberately. Overlapping shapes and edges cutting through boxes are the most common reasons a generated diagram looks broken.

- Pick one direction of flow (top-to-bottom for processes and hierarchies, left-to-right for pipelines and request paths) and keep to it.
- Put shapes in rows and columns on the 10px grid. Use consistent sizes (e.g. 120x60 or 160x60 boxes), with at least 40px between shapes and 80–140px between levels.
- Centre a parent over its children: parent centre x = midpoint of the first and last child centres. To space `n` items of width `w` evenly across a width `W`, the gap is `(W - n*w) / (n + 1)`.
- Size containers to fit their children with 20px padding, plus the header height (`startSize`) at the top.
- Put side branches (error paths, "No" outcomes) in their own column. Route edges that would cross the main path with waypoints.
- Keep labels short. Set the box width rather than relying on wrapping to fit long text; about 7px per character at fontSize 12.
- For more than about 25 shapes, split into pages (one `<diagram>` each) or group into containers.

## Conventions

- File extension: `.drawio` (plain XML). `.drawio.svg` / `.drawio.png` embed the same XML for doc-embeddable, previewable diagrams; use those only if the user needs the diagram inline in a README or doc.
- Filenames: descriptive and kebab/lowercase, e.g. `payment-service-architecture.drawio`, `user-onboarding-flowchart.drawio`.
- IDs: short, descriptive, unique within the file (`router`, `ws1`, `e-switch-ws1`) rather than opaque UUIDs — makes diffs and later edits legible.
- When editing an existing `.drawio` file, preserve unrelated cells exactly; only touch the `mxCell` elements you intend to change, and never split an element's opening/closing tags across separate edits.

## Escaping text

Labels and attribute values are XML. Escape `&` as `&amp;`, `<` as `&lt;`, `>` as `&gt;` and `"` as `&quot;`, including text copied from the user or a file. With `html=1` in the style, a literal `<` in a label must be `&lt;` twice-escaped as `&amp;lt;`. Never put unescaped user text in an `value="..."` attribute.

## Validation checklist

Before treating a diagram as finished, confirm:

- [ ] `scripts/validate_drawio.py` reports OK. It checks well-formed XML, unique ids, the root and layer cells, that every `parent` and every edge `source`/`target` exists (a connector may also end on another connector, never on `"0"` or a layer), vertex/edge flags, geometry, and missing `;` in styles
- [ ] Nested cells use their container's id as `parent` and container-relative coordinates
- [ ] No shapes overlap unintentionally, and children sit inside their container's bounds
- [ ] Labels fit their shapes. Text from the user is escaped (see above)
- [ ] The same kind of element looks the same everywhere (shape, colour, size)

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| File won't open | Malformed XML — check unclosed tags/quotes |
| Shape not visible | Missing `vertex="1"`, or a `parent` id that doesn't exist |
| Shape appears far from its container | Child `x`/`y` written in page coordinates instead of relative to the container |
| Connector not attached | `source`/`target` id doesn't match an existing cell |
| `<diagram>` holds unreadable text | Compressed page: run `scripts/decompress_drawio.py` |
| Style not applied | Missing `;` separator between style properties |
| Text not wrapping | Add `whiteSpace=wrap;html=1;` to the style |
| Image shape missing | Check exact library path/filename (case-sensitive) |

## Bundled resources

- `scripts/validate_drawio.py` — structural validator: `python3 <skill-dir>/scripts/validate_drawio.py FILE...`. Exits 1 and prints one line per issue. Standard library only
- `scripts/decompress_drawio.py` — turns compressed pages into plain XML: `python3 <skill-dir>/scripts/decompress_drawio.py FILE --in-place` (or `-o OUT`)
- `scripts/drawio_io.py` — shared file-reading helpers used by both scripts
- `scripts/layout_drawio.py` — lays out a graph spec (JSON written from a Mermaid diagram) and writes a `.drawio` file: `python3 <skill-dir>/scripts/layout_drawio.py SPEC.json -o OUT.drawio`. Its helpers: `scripts/graph_spec.py` (spec parsing and checks), `scripts/layered_layout.py` (layered graph layout), `scripts/graph_render.py` (flowchart, state, class and ER diagrams), `scripts/sequence_render.py` (sequence diagrams), `scripts/drawio_writer.py` (XML output) and `scripts/text_metrics.py` (label sizing)
- `scripts/render_drawio_svg.py` — renders a `.drawio` file as an editable `.drawio.svg` (an SVG image that carries the diagram, so GitHub/GitLab show it and draw.io opens it), without the draw.io app: `python3 <skill-dir>/scripts/render_drawio_svg.py IN.drawio -o OUT.drawio.svg`
- `references/format-reference.md` — XML structure in full: pages, cells, parents (layers, containers, edge labels), absolute and relative geometry, waypoints, `UserObject` custom properties, compressed pages. Read it for anything nested or unusual
- `references/style-reference.md` — every style property (fill, stroke, text, edges, arrows including ER ends, containers, images, named styles)
- `assets/examples/*.drawio` — one complete example per diagram type (table above)

## Editor preview (optional)

If working in VS Code, the **Draw.io Integration** extension (`hediet.vscode-drawio`) opens `.drawio`/`.drawio.svg`/`.drawio.png` files in a visual editor for human review — useful for the user to sanity-check a generated diagram, not required to generate one.
