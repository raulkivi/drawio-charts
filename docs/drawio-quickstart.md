# Draw.io Quick Start Guide

## File Formats

| Format | Extension | Best For |
|--------|-----------|----------|
| Standard | `.drawio` | General use, version control |
| Editable SVG | `.drawio.svg` | Embedding in docs, GitHub READMEs |
| Editable PNG | `.drawio.png` | When SVG not supported |
| HTML | `.html` | Web sharing with redirect |

## Basic XML Structure

```xml
<mxfile host="app.diagrams.net">
  <diagram id="unique-id" name="Page 1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>                    <!-- Root cell -->
        <mxCell id="1" parent="0"/>         <!-- Default layer -->
        
        <!-- Your shapes and connectors here -->
        
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Creating Shapes (Vertices)

```xml
<mxCell id="2" value="My Shape" 
        style="rounded=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" 
        parent="1" vertex="1">
  <mxGeometry x="100" y="50" width="120" height="60" as="geometry"/>
</mxCell>
```

**Required attributes:**
- `id` - Unique identifier
- `parent="1"` - Parent is default layer
- `vertex="1"` - Marks as shape

## Creating Connectors (Edges)

```xml
<mxCell id="3" value="" 
        style="endArrow=classic;" 
        parent="1" source="2" target="4" edge="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

**Required attributes:**
- `id` - Unique identifier  
- `parent="1"` - Parent is default layer
- `edge="1"` - Marks as connector
- `source`, `target` - Connected shape IDs

## Common Styles Quick Reference

### Shapes
```
fillColor=#dae8fc        # Background color
strokeColor=#6c8ebf      # Border color
strokeWidth=2            # Border thickness
rounded=1                # Rounded corners
shape=ellipse            # Circle/oval
shape=rhombus            # Diamond
```

### Text
```
fontColor=#333333        # Text color
fontSize=14              # Text size
fontStyle=1              # 1=bold, 2=italic, 3=both
align=center             # left, center, right
whiteSpace=wrap          # Enable wrapping
```

### Connectors
```
endArrow=classic         # Arrow at end
startArrow=none          # No arrow at start
edgeStyle=orthogonalEdgeStyle  # Right-angle routing
curved=1                 # Curved line
dashed=1                 # Dashed line
```

## Shape Library Examples

### Basic Shapes
```xml
<!-- Rectangle -->
<mxCell style="rounded=0;" .../>

<!-- Rounded Rectangle -->
<mxCell style="rounded=1;" .../>

<!-- Circle -->
<mxCell style="ellipse;aspect=fixed;" .../>

<!-- Diamond -->
<mxCell style="rhombus;" .../>
```

### Network/IT Shapes
```xml
<!-- Server -->
<mxCell style="shape=mxgraph.computers.server;" .../>

<!-- Laptop -->
<mxCell style="shape=mxgraph.computers.laptop;" .../>

<!-- Database -->
<mxCell style="shape=cylinder3;size=15;" .../>

<!-- Cloud -->
<mxCell style="ellipse;shape=cloud;" .../>
```

### Using Images
```xml
<!-- SVG from library -->
<mxCell style="image;image=img/lib/mscae/VirtualMachine.svg;aspect=fixed;" .../>

<!-- External image -->
<mxCell style="image;image=https://example.com/icon.png;" .../>
```

## Complete Example: Simple Flowchart

```xml
<mxfile host="app.diagrams.net">
  <diagram id="flowchart" name="Simple Flow">
    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        
        <!-- Start -->
        <mxCell id="start" value="Start" 
                style="ellipse;fillColor=#d5e8d4;strokeColor=#82b366;" 
                parent="1" vertex="1">
          <mxGeometry x="100" y="50" width="80" height="40" as="geometry"/>
        </mxCell>
        
        <!-- Process -->
        <mxCell id="process" value="Do Something" 
                style="rounded=0;fillColor=#dae8fc;strokeColor=#6c8ebf;" 
                parent="1" vertex="1">
          <mxGeometry x="80" y="130" width="120" height="60" as="geometry"/>
        </mxCell>
        
        <!-- End -->
        <mxCell id="end" value="End" 
                style="ellipse;fillColor=#f8cecc;strokeColor=#b85450;" 
                parent="1" vertex="1">
          <mxGeometry x="100" y="230" width="80" height="40" as="geometry"/>
        </mxCell>
        
        <!-- Connectors -->
        <mxCell id="e1" style="endArrow=classic;" 
                parent="1" source="start" target="process" edge="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        
        <mxCell id="e2" style="endArrow=classic;" 
                parent="1" source="process" target="end" edge="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Tips

1. **ID Management**: Use descriptive IDs for easier maintenance
2. **Styles**: Combine multiple styles with semicolons
3. **Positioning**: x,y coordinates are from top-left corner
4. **Layers**: All diagram cells should have `parent="1"`
5. **Colors**: Use hex colors (#RRGGBB) or `none`

## VS Code Integration

Install the **Draw.io Integration** extension:
- Extension ID: `hediet.vscode-drawio`
- Opens `.drawio` files in visual editor
- Supports `.drawio.svg` and `.drawio.png`

## Resources

- [Official Documentation](https://www.drawio.com/doc/)
- [mxGraph Manual](https://jgraph.github.io/mxgraph/docs/manual.html)
- [GitHub Repository](https://github.com/jgraph/drawio)
