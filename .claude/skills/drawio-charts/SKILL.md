---
name: drawio-charts
description: Create, edit, and validate draw.io (diagrams.net) .drawio XML diagrams — flowcharts, system/network architecture diagrams, org charts, sequence diagrams, ER diagrams. Use whenever the user asks to create or modify a draw.io diagram, chart, or .drawio file, or wants to visualize an architecture, process, or network as a diagram.
---

# draw.io Chart Creation

Generate and edit `.drawio` files directly as XML — no draw.io application is required to produce a valid diagram. The XML format (`mxfile` / `mxGraphModel` / `mxCell`) is documented in full under `references/`; this file covers what's needed for the common case.

## Workflow

1. Clarify the diagram type and content (flowchart, architecture, network, org chart, ER, sequence) and the entities/relationships to represent.
2. Pick a file path ending in `.drawio` (see Conventions below).
3. Write the XML starting from the skeleton below, adding one `mxCell` per shape and one per connector.
4. Apply styling from the cheatsheet — stay consistent (same shape type / palette entry for same kind of element).
5. Run through the Validation checklist before considering the diagram done.
6. If the user has the `hediet.vscode-drawio` VS Code extension, mention they can open the file to visually confirm it — but don't depend on it to verify correctness.

## Minimal file skeleton

```xml
<mxfile host="app.diagrams.net" modified="2026-01-01T00:00:00.000Z" agent="draw.io" version="21.0.0">
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

Required attributes: every cell needs a unique `id` and `parent="1"` (the default layer). Shapes need `vertex="1"` plus an `mxGeometry` with `x`/`y`/`width`/`height`. Connectors need `edge="1"` plus `source`/`target` ids that match existing vertex ids, and a `relative="1"` geometry (add waypoints via a nested `<Array as="points"><mxPoint .../></Array>` if needed — see `references/mxgeometry-api-reference.md`).

To equally space `n` items of `item_width` across a container of `container_width`: gap = `(container_width - n * item_width) / (n + 1)`.

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

## Conventions

- File extension: `.drawio` (plain XML). `.drawio.svg` / `.drawio.png` embed the same XML for doc-embeddable, previewable diagrams; use those only if the user needs the diagram inline in a README or doc.
- Filenames: descriptive and kebab/lowercase, e.g. `payment-service-architecture.drawio`, `user-onboarding-flowchart.drawio`.
- IDs: short, descriptive, unique within the file (`router`, `ws1`, `e-switch-ws1`) rather than opaque UUIDs — makes diffs and later edits legible.
- When editing an existing `.drawio` file, preserve unrelated cells exactly; only touch the `mxCell` elements you intend to change, and never split an element's opening/closing tags across separate edits.

## Validation checklist

Before treating a diagram as finished, confirm:

- [ ] XML is well-formed (every tag closed, attributes quoted)
- [ ] Every `mxCell` id is unique within the file
- [ ] Every shape has `vertex="1"`; every connector has `edge="1"`
- [ ] Every connector's `source`/`target` matches an existing vertex `id`
- [ ] `parent="1"` on all diagram-level cells (`"0"`/`"1"` are the reserved root/layer ids)
- [ ] Style strings use `;` between properties (a missing `;` silently drops the next property)

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| File won't open | Malformed XML — check unclosed tags/quotes |
| Shape not visible | Missing `vertex="1"` |
| Connector not attached | `source`/`target` id doesn't match an existing vertex |
| Style not applied | Missing `;` separator between style properties |
| Text not wrapping | Add `whiteSpace=wrap;html=1;` to the style |
| Image shape missing | Check exact library path/filename (case-sensitive) |

## Reference material

- `references/format-reference.md` — full `mxfile`/`mxGraphModel`/`mxCell` XML structure, file extensions, special cell ids
- `references/style-reference.md` — complete style property tables (fill, stroke, text, edges, containers, images, arrow types, edge routing)
- `references/mxcell-api-reference.md` — `mxCell` JS API, for anyone scripting diagram generation against the mxGraph library itself
- `references/mxgeometry-api-reference.md` — `mxGeometry` JS API: absolute/relative positioning, edge waypoints, label offsets
- `assets/examples/company-network.drawio` — complete worked example diagram

## Editor preview (optional)

If working in VS Code, the **Draw.io Integration** extension (`hediet.vscode-drawio`) opens `.drawio`/`.drawio.svg`/`.drawio.png` files in a visual editor for human review — useful for the user to sanity-check a generated diagram, not required to generate one.
