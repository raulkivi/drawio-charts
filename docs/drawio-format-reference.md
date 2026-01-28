# Draw.io File Format Reference

## Overview

Draw.io (diagrams.net) uses an XML-based file format built on **mxGraph**, an open-source JavaScript diagramming library. The format is well-documented and the entire stack is open source.

## File Extensions

| Extension | Description |
|-----------|-------------|
| `.drawio` | Standard XML format |
| `.drawio.svg` | SVG with embedded diagram data in `content` attribute |
| `.drawio.png` | PNG with embedded diagram data |
| `.dio` | Alternative extension for standard format |

## XML Structure

### Root Element: `<mxfile>`

```xml
<mxfile host="app.diagrams.net" modified="2026-01-26T12:00:00.000Z" agent="draw.io" version="21.0.0">
  <diagram id="unique-id" name="Diagram Name">
    <mxGraphModel>
      <!-- graph content -->
    </mxGraphModel>
  </diagram>
</mxfile>
```

### Graph Model: `<mxGraphModel>`

Attributes:
- `dx`, `dy` - Canvas offset
- `grid` - Show grid (1/0)
- `gridSize` - Grid cell size
- `guides` - Enable guides (1/0)
- `tooltips` - Enable tooltips (1/0)
- `connect` - Enable connections (1/0)
- `arrows` - Show arrows (1/0)
- `fold` - Enable folding (1/0)
- `page` - Show page (1/0)
- `pageScale` - Page scale factor
- `pageWidth`, `pageHeight` - Page dimensions

### Cells: `<mxCell>`

Every element (vertex, edge, group) is an `mxCell`:

```xml
<mxCell id="unique-id" value="Label" style="..." parent="1" vertex="1">
  <mxGeometry x="20" y="20" width="80" height="30" as="geometry"/>
</mxCell>
```

#### Key Attributes:
- `id` - Unique identifier
- `value` - Label/content (can be HTML)
- `style` - Semicolon-separated style properties
- `parent` - Parent cell ID (usually "1" for root)
- `vertex="1"` - Marks as vertex (shape)
- `edge="1"` - Marks as edge (connector)
- `source`, `target` - For edges, the connected vertex IDs

### Geometry: `<mxGeometry>`

```xml
<mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
```

For edges with waypoints:
```xml
<mxGeometry relative="1" as="geometry">
  <Array as="points">
    <mxPoint x="200" y="150"/>
  </Array>
</mxGeometry>
```

## Style Properties

Styles are semicolon-separated key=value pairs:

```
shape=rectangle;fillColor=#dae8fc;strokeColor=#6c8ebf;rounded=1;
```

### Common Style Properties:

| Property | Description | Example |
|----------|-------------|---------|
| `shape` | Shape type | `rectangle`, `ellipse`, `rhombus` |
| `fillColor` | Background color | `#ffffff`, `none` |
| `strokeColor` | Border color | `#000000` |
| `strokeWidth` | Border width | `2` |
| `rounded` | Rounded corners | `0` or `1` |
| `dashed` | Dashed line | `0` or `1` |
| `dashPattern` | Dash pattern | `8 8` |
| `opacity` | Transparency | `0-100` |
| `fontColor` | Text color | `#000000` |
| `fontSize` | Text size | `12` |
| `fontStyle` | Bold/italic | `1`=bold, `2`=italic, `3`=both |
| `align` | Horizontal align | `left`, `center`, `right` |
| `verticalAlign` | Vertical align | `top`, `middle`, `bottom` |
| `html` | HTML labels | `1` |

### Edge-Specific Styles:

| Property | Description | Example |
|----------|-------------|---------|
| `endArrow` | Arrow at target | `classic`, `block`, `none` |
| `startArrow` | Arrow at source | `classic`, `none` |
| `edgeStyle` | Routing style | `orthogonalEdgeStyle`, `elbowEdgeStyle` |
| `curved` | Curved lines | `1` |

## Built-in Shapes

### Basic Shapes:
- `rectangle`, `ellipse`, `rhombus`, `triangle`, `hexagon`
- `cylinder`, `actor`, `cloud`, `document`

### Stencil Libraries:
Draw.io includes many shape libraries accessible via style:

```
shape=mxgraph.cisco.switches.workgroup_switch
shape=mxgraph.computers.laptop
image=img/lib/mscae/VirtualMachine.svg
```

## Special Cell IDs

- `"0"` - Root cell (invisible, parent of all)
- `"1"` - Default layer (parent for most diagram cells)

## Resources

### Official Documentation:
- [diagrams.net Documentation](https://www.drawio.com/doc/)
- [GitHub Repository](https://github.com/jgraph/drawio) (Apache 2.0 License)

### mxGraph (underlying library):
- [mxGraph Manual](https://jgraph.github.io/mxgraph/docs/manual.html)
- [mxGraph GitHub](https://github.com/jgraph/mxgraph) (Apache 2.0 License)

### Key Source Files:
- `mxClient.js` - Main JavaScript library
- `mxGraphModel` - Graph data structure
- `mxCell` - Cell (vertex/edge) class
- `mxGeometry` - Positioning and sizing
- `mxStylesheet` - Style management

## License

- **Draw.io**: Apache 2.0 License
- **mxGraph**: Apache 2.0 License
- Both are fully open source and actively maintained by JGraph Ltd.
