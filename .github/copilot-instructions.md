# Copilot Instructions for Draw.io Charts Workspace

## Overview

This workspace is for creating and managing draw.io diagrams programmatically. Use the documentation in `diagrams/docs/` to understand the XML format and create valid diagrams.

## Documentation Reference

| Document | Use For |
|----------|---------|
| `diagrams/docs/drawio-quickstart.md` | Basic structure and quick examples |
| `diagrams/docs/drawio-format-reference.md` | XML structure and file formats |
| `diagrams/docs/drawio-style-reference.md` | All style properties (colors, shapes, text, edges) |
| `diagrams/docs/mxcell-api-reference.md` | Understanding mxCell elements |
| `diagrams/docs/mxgeometry-api-reference.md` | Positioning and geometry |

## Creating Draw.io Diagrams

### File Structure

Always start with this XML skeleton:

```xml
<mxfile host="app.diagrams.net" modified="YYYY-MM-DDTHH:MM:SS.000Z" agent="draw.io" version="21.0.0">
  <diagram id="unique-id" name="Diagram Name">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1100" pageHeight="850">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- Add shapes and connectors here -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### Creating Shapes (Vertices)

```xml
<mxCell id="unique-id" value="Label Text" 
        style="shape=rectangle;fillColor=#dae8fc;strokeColor=#6c8ebf;rounded=1;" 
        parent="1" vertex="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
</mxCell>
```

**Required attributes:**
- `id` - Must be unique within the diagram
- `parent="1"` - Always use "1" for the default layer
- `vertex="1"` - Marks this as a shape

### Creating Connectors (Edges)

```xml
<mxCell id="edge-id" value="" 
        style="endArrow=classic;strokeColor=#666666;" 
        parent="1" source="source-id" target="target-id" edge="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

**Required attributes:**
- `id` - Must be unique
- `parent="1"` - Default layer
- `edge="1"` - Marks as connector
- `source`, `target` - IDs of connected shapes

## Common Style Patterns

### Shape Styles
```
fillColor=#dae8fc        # Light blue background
strokeColor=#6c8ebf      # Blue border
strokeWidth=2            # Border thickness
rounded=1                # Rounded corners
shape=ellipse            # Circle
shape=rhombus            # Diamond
shape=cylinder3          # Database cylinder
```

### Text Styles
```
fontColor=#333333        # Dark gray text
fontSize=12              # Font size
fontStyle=1              # Bold (1=bold, 2=italic, 3=both)
align=center             # Horizontal alignment
verticalAlign=middle     # Vertical alignment
whiteSpace=wrap          # Enable text wrapping
```

### Edge Styles
```
endArrow=classic         # Arrow at target
startArrow=none          # No arrow at source
edgeStyle=orthogonalEdgeStyle  # Right-angle routing
curved=1                 # Curved connector
dashed=1                 # Dashed line
```

## Shape Libraries

### Active Directory Shapes (Recommended for Network Diagrams)
```
image=img/lib/active_directory/laptop_client.svg
image=img/lib/active_directory/domain_controller.svg
image=img/lib/active_directory/database_server.svg
image=img/lib/active_directory/generic_server.svg
image=img/lib/active_directory/switch.svg
image=img/lib/active_directory/router.svg
image=img/lib/active_directory/firewall.svg
image=img/lib/active_directory/internet_cloud.svg
image=img/lib/active_directory/workstation_client.svg
image=img/lib/active_directory/web_server.svg
image=img/lib/active_directory/cluster_server.svg
```

### MSCAE (Microsoft Cloud Architecture) Shapes
```
image=img/lib/mscae/Active_Directory.svg
image=img/lib/mscae/SQL_Database_generic.svg
image=img/lib/mscae/Virtual_Machine.svg
image=img/lib/mscae/Virtual_Network.svg
image=img/lib/mscae/Monitor.svg
image=img/lib/mscae/Client_Apps.svg
image=img/lib/mscae/Storage.svg
image=img/lib/mscae/Kubernetes_Services.svg
```

### Network/IT Shapes (mxgraph)
```
shape=mxgraph.computers.laptop
shape=mxgraph.computers.server
shape=mxgraph.cisco.switches.workgroup_switch
```

### Basic Shapes
```
shape=rectangle          # Default
shape=ellipse            # Circle/oval
shape=rhombus            # Diamond
shape=cylinder3          # Cylinder
shape=hexagon            # Hexagon
shape=triangle           # Triangle
```

## File Naming Conventions

| Type | Location | Extension |
|------|----------|-----------|
| Editable diagram | `diagrams/` subdirectories | `.drawio` |
| Editable SVG | `diagrams/` or `exports/` | `.drawio.svg` |
| Export only | `exports/` | `.svg`, `.png`, `.pdf` |

## Diagram Organization

```
diagrams/
├── architecture/     # System architecture diagrams
├── flowcharts/       # Process flows, decision trees
├── sequences/        # Sequence diagrams, user flows
└── templates/        # Reusable diagram templates
```

## Best Practices

1. **Unique IDs**: Use descriptive, unique IDs for all cells
2. **Consistent styling**: Use the same colors for similar elements
3. **Proper hierarchy**: All diagram cells use `parent="1"`
4. **Comments**: Add XML comments for complex diagrams
5. **Validation**: Ensure XML is well-formed before saving

## Color Palette (Recommended)

| Purpose | Fill | Stroke |
|---------|------|--------|
| Default/Neutral | `#f5f5f5` | `#666666` |
| Primary/Info | `#dae8fc` | `#6c8ebf` |
| Success/Start | `#d5e8d4` | `#82b366` |
| Warning | `#fff2cc` | `#d6b656` |
| Error/End | `#f8cecc` | `#b85450` |
| Purple/Special | `#e1d5e7` | `#9673a6` |

## Testing Diagrams

After creating a `.drawio` file:
1. Open in VS Code with Draw.io Integration extension
2. Verify all shapes render correctly
3. Check all connectors are attached properly
4. Validate text labels display as expected

## Troubleshooting

| Issue | Solution |
|-------|----------|
| File won't open | Check XML is well-formed, validate closing tags |
| Shape not visible | Verify `vertex="1"` attribute present |
| Connector not connecting | Check `source` and `target` IDs exist |
| Style not applied | Ensure semicolons separate style properties |
| Text not wrapping | Add `whiteSpace=wrap;html=1;` to style |
| Image shape missing | Verify exact file name (case-sensitive), check library path |
| File corrupted after edit | Recreate file from scratch with valid XML skeleton |

## Style Templates for Image Shapes

### Active Directory / MSCAE Image Style
```
image;aspect=fixed;perimeter=ellipsePerimeter;html=1;align=center;shadow=0;dashed=0;spacingTop=3;image=img/lib/active_directory/[shape].svg;labelPosition=center;verticalLabelPosition=bottom;verticalAlign=top;fontSize=11;
```

### Sketch-style MSCAE Image
```
sketch=0;aspect=fixed;html=1;points=[];align=center;fontSize=11;image=img/lib/mscae/[shape].svg;labelPosition=center;verticalLabelPosition=bottom;verticalAlign=top;
```

## Tips for Programmatic Edits

1. **Avoid partial XML edits** - Always include complete mxCell elements when editing
2. **Use unique IDs** - Duplicate IDs cause rendering issues
3. **Preserve XML structure** - Never split opening/closing tags across edits
4. **Test after edits** - Open diagram in draw.io to verify changes
5. **Calculate positions** - For equal spacing: `(container_width - (n * item_width)) / (n + 1)`
