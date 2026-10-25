# draw.io File Format Reference

draw.io (diagrams.net) stores diagrams as XML built on **mxGraph**. This file covers everything needed to write that XML by hand: file structure, cells, parents, geometry, compressed pages and custom properties. For style strings see `style-reference.md`.

## Contents

- [File extensions](#file-extensions)
- [Document structure](#document-structure)
- [Cells](#cells)
- [Parents: root, layers, containers, edge labels](#parents-root-layers-containers-edge-labels)
- [Geometry](#geometry)
- [Custom properties (UserObject)](#custom-properties-userobject)
- [Compressed pages](#compressed-pages)
- [Resources](#resources)

## File extensions

| Extension | Description |
|-----------|-------------|
| `.drawio` | Plain XML (use this by default) |
| `.dio` | Older alias for `.drawio` |
| `.drawio.svg` | SVG image with the diagram XML embedded in its `content` attribute |
| `.drawio.png` | PNG image with the diagram XML embedded in a text chunk |

## Document structure

```xml
<mxfile host="app.diagrams.net" agent="draw.io" version="21.0.0">
  <diagram id="overview" name="Overview">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1"
                  connect="1" arrows="1" fold="1" page="1" pageScale="1"
                  pageWidth="1100" pageHeight="850">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- cells -->
      </root>
    </mxGraphModel>
  </diagram>
  <!-- more <diagram> elements = more pages -->
</mxfile>
```

- Each `<diagram>` is a page. Page `id`s must be unique within the file; cell ids only need to be unique within their page.
- `mxfile` attributes (`host`, `modified`, `agent`, `version`) are informational. Omit `modified` rather than inventing a timestamp.
- `mxGraphModel` attributes: `dx`/`dy` canvas scroll offset, `grid`/`gridSize` grid display and snap, `guides`, `tooltips`, `connect`, `arrows`, `fold` editor toggles (1/0), `page` show page boundary, `pageScale`, `pageWidth`/`pageHeight` page size in px (Letter landscape is 1100x850, A4 landscape 1169x827).
- A bare `<mxGraphModel>` as the document root (no `mxfile`) also opens, as a single page.

## Cells

Every shape, connector, label, container and layer is an `mxCell`.

| Attribute | Meaning |
|-----------|---------|
| `id` | Unique within the page |
| `value` | Label text. With `html=1` in the style it is HTML, so it is escaped twice (see SKILL.md) |
| `style` | `key=value;` pairs and bare named styles, see `style-reference.md` |
| `parent` | Id of the containing cell, see next section |
| `vertex="1"` | A shape (includes text boxes, containers, groups, edge labels) |
| `edge="1"` | A connector |
| `source` / `target` | On edges: id of the cell each end attaches to (a vertex, or another edge) |
| `connectable="0"` | Edges can't attach to this cell (used on edge labels and table rows) |
| `collapsed="1"` | Container shown collapsed |

A content cell is exactly one of `vertex="1"` or `edge="1"`.

## Parents: root, layers, containers, edge labels

The cell tree has four levels:

| Parent | Child | Example |
|--------|-------|---------|
| none | the root cell, always `id="0"` | `<mxCell id="0"/>` |
| `"0"` | a layer. `"1"` is the default; add more for toggleable overlays | `<mxCell id="notes" value="Notes" parent="0"/>` |
| a layer | top-level shapes and connectors | `parent="1"` |
| a container, group, table or edge | nested shapes, rows, edge labels | `parent="vpc"`, `parent="e1"` |

- **Containers** (`container=1`, `swimlane`, `group`, `table`): children use the container's id as `parent`, and their `x`/`y` are **relative to the container's top-left corner**, not the page. Moving the container moves them.
- **Edge labels**: a label floating on a connector is a vertex with `parent="<edge id>"`, a `relative="1"` geometry and no width/height (see [Edge label positioning](#edge-label-positioning)). A simple label can instead go in the edge's own `value`.
- An edge's `parent` is normally the lowest common container of its two ends (often just `"1"`).
- Never point `source`/`target` at `"0"` or a layer.

## Geometry

Every vertex and edge has one `<mxGeometry ... as="geometry"/>` child.

### Vertex geometry

```xml
<mxGeometry x="120" y="80" width="100" height="60" as="geometry"/>
```

`x`/`y` are the top-left corner, relative to the parent (the page for layer children, the container for nested cells). Units are px; keep values on the 10px grid.

With `relative="1"` a vertex is positioned as a fraction of its parent's size: `x`/`y` from 0 to 1, plus an optional pixel `offset`. To centre a 40x40 badge on its parent:

```xml
<mxGeometry x="0.5" y="0.5" width="40" height="40" relative="1" as="geometry">
  <mxPoint x="-20" y="-20" as="offset"/>
</mxGeometry>
```

### Edge geometry

Connected edges need only `<mxGeometry relative="1" as="geometry"/>`; draw.io routes them. Add waypoints to force a path:

```xml
<mxGeometry relative="1" as="geometry">
  <Array as="points">
    <mxPoint x="200" y="120"/>
    <mxPoint x="200" y="200"/>
  </Array>
</mxGeometry>
```

An end not attached to a cell uses a fixed point instead of `source`/`target` (sequence diagram lifelines, free-standing lines):

```xml
<mxCell id="line" style="endArrow=none;dashed=1;" parent="1" edge="1">
  <mxGeometry relative="1" as="geometry">
    <mxPoint x="150" y="100" as="sourcePoint"/>
    <mxPoint x="150" y="500" as="targetPoint"/>
  </mxGeometry>
</mxCell>
```

### Edge label positioning

For an edge-label vertex (and an edge's own label), the relative geometry means: `x` is the position along the edge from -1 (source end) through 0 (middle) to 1 (target end); `y` is a perpendicular offset in px; an `offset` point adds a further px shift.

```xml
<mxCell id="e1-label" value="yes" style="edgeLabel;html=1;align=center;verticalAlign=middle;"
        parent="e1" vertex="1" connectable="0">
  <mxGeometry x="-0.5" y="10" relative="1" as="geometry">
    <mxPoint as="offset"/>
  </mxGeometry>
</mxCell>
```

### Offsets

| Cell | `offset` means |
|------|----------------|
| Edge label | px shift from the computed position along the edge |
| Relative vertex | px shift from the relative position |
| Absolute vertex | px shift of the label inside the shape |

## Custom properties (UserObject)

To attach data (owner, URL, tags) to a shape, wrap the `mxCell` in a `UserObject` (older files use `object`). The wrapper holds the `id`, the `label` (instead of `value`) and any custom attributes; the inner `mxCell` has no `id`.

```xml
<UserObject id="api" label="Orders API" owner="team-payments" link="https://wiki.example.com/orders">
  <mxCell style="rounded=1;whiteSpace=wrap;html=1;" parent="1" vertex="1">
    <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
  </mxCell>
</UserObject>
```

Use `placeholders=1` in the style to show attributes in the label, e.g. `label="%owner%"`. A `link` attribute makes the shape clickable.

## Compressed pages

draw.io may save a page as text instead of an `<mxGraphModel>` child:

```xml
<diagram id="p1" name="Page-1">7VZNb9swDP01Ph...</diagram>
```

That text is `base64(raw-deflate(encodeURIComponent(xml)))`. It can't be edited directly. Convert it to plain XML first; draw.io opens either form:

```bash
python3 scripts/decompress_drawio.py diagram.drawio --in-place
```

## Resources

- [diagrams.net documentation](https://www.drawio.com/doc/) and [source](https://github.com/jgraph/drawio) (Apache-2.0)
- [mxGraph manual](https://jgraph.github.io/mxgraph/docs/manual.html) and [JS API](https://jgraph.github.io/mxgraph/docs/js-api/files/index-txt.html) (Apache-2.0), for scripting diagrams in JavaScript rather than writing XML
