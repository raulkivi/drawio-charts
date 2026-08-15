# Draw.io Style Reference

## Overview

Styles in draw.io are semicolon-separated key=value pairs that control the visual appearance of cells. A style string can include named styles and/or individual property overrides.

## Style String Format

```
[stylename;][key1=value1;][key2=value2;]...
```

### Examples

```
rounded=1;fillColor=#dae8fc;strokeColor=#6c8ebf;
```

```
defaultVertex;fillColor=#f5f5f5;
```

```
shape=ellipse;whiteSpace=wrap;html=1;aspect=fixed;
```

## Shape Styles

### Basic Shapes

| Style Value | Description |
|-------------|-------------|
| `shape=rectangle` | Rectangle (default for vertices) |
| `shape=ellipse` | Ellipse/Circle |
| `shape=rhombus` | Diamond |
| `shape=triangle` | Triangle |
| `shape=hexagon` | Hexagon |
| `shape=parallelogram` | Parallelogram |
| `shape=trapezoid` | Trapezoid |
| `shape=cylinder` | Cylinder (database) |
| `shape=actor` | Stick figure |
| `shape=cloud` | Cloud shape |
| `shape=document` | Document with wavy bottom |
| `shape=note` | Note/sticky note |
| `shape=folder` | Folder |
| `shape=card` | Card with folded corner |
| `shape=tape` | Tape/banner |
| `shape=cube` | 3D Cube |
| `shape=step` | Step/chevron |
| `shape=process` | Process (rectangle with bars) |
| `shape=callout` | Callout/speech bubble |

### Special Shapes

| Style Value | Description |
|-------------|-------------|
| `shape=image` | Image shape (use with `image=URL`) |
| `shape=label` | Label shape |
| `shape=swimlane` | Swimlane container |
| `shape=table` | Table |
| `shape=partialRectangle` | Partial rectangle |

### Extended Shape Libraries

```
shape=mxgraph.basic.rect
shape=mxgraph.flowchart.decision
shape=mxgraph.cisco.switches.workgroup_switch
shape=mxgraph.computers.laptop
shape=mxgraph.aws3.ec2
```

## Fill Styles

| Property | Values | Description |
|----------|--------|-------------|
| `fillColor` | `#RRGGBB`, `none` | Background color |
| `fillOpacity` | `0-100` | Fill transparency |
| `gradientColor` | `#RRGGBB`, `none` | Gradient end color |
| `gradientDirection` | `north`, `south`, `east`, `west` | Gradient direction |
| `opacity` | `0-100` | Overall opacity |

### Examples

```
fillColor=#dae8fc;
fillColor=none;
fillColor=#dae8fc;gradientColor=#7ea6e0;gradientDirection=south;
```

## Stroke (Border) Styles

| Property | Values | Description |
|----------|--------|-------------|
| `strokeColor` | `#RRGGBB`, `none` | Border color |
| `strokeWidth` | number | Border width in pixels |
| `strokeOpacity` | `0-100` | Border transparency |
| `dashed` | `0`, `1` | Dashed line |
| `dashPattern` | `n n` | Dash pattern (e.g., `8 8`) |
| `rounded` | `0`, `1` | Rounded corners |
| `arcSize` | number | Corner radius |

### Examples

```
strokeColor=#6c8ebf;strokeWidth=2;
dashed=1;dashPattern=8 8;
rounded=1;arcSize=10;
```

## Text/Label Styles

| Property | Values | Description |
|----------|--------|-------------|
| `fontColor` | `#RRGGBB` | Text color |
| `fontSize` | number | Font size in points |
| `fontFamily` | string | Font name |
| `fontStyle` | `0-7` | Font style bitmask |
| `align` | `left`, `center`, `right` | Horizontal alignment |
| `verticalAlign` | `top`, `middle`, `bottom` | Vertical alignment |
| `labelPosition` | `left`, `center`, `right` | Label horizontal position |
| `verticalLabelPosition` | `top`, `middle`, `bottom` | Label vertical position |
| `labelBackgroundColor` | `#RRGGBB`, `none` | Label background |
| `labelBorderColor` | `#RRGGBB`, `none` | Label border |
| `spacingTop` | number | Top padding |
| `spacingBottom` | number | Bottom padding |
| `spacingLeft` | number | Left padding |
| `spacingRight` | number | Right padding |
| `spacing` | number | All-side padding |
| `horizontal` | `0`, `1` | Horizontal text (vs vertical) |
| `whiteSpace` | `wrap` | Enable text wrapping |
| `html` | `1` | Enable HTML in labels |
| `overflow` | `hidden`, `visible`, `fill`, `width` | Text overflow behavior |

### Font Style Values

| Value | Style |
|-------|-------|
| `0` | Normal |
| `1` | Bold |
| `2` | Italic |
| `3` | Bold + Italic |
| `4` | Underline |
| `5` | Bold + Underline |
| `6` | Italic + Underline |
| `7` | Bold + Italic + Underline |

### Examples

```
fontColor=#333333;fontSize=14;fontStyle=1;
align=left;verticalAlign=top;spacingLeft=10;
whiteSpace=wrap;html=1;overflow=hidden;
```

## Edge (Connector) Styles

### Arrow Styles

| Property | Values | Description |
|----------|--------|-------------|
| `endArrow` | arrow type | Arrow at target end |
| `startArrow` | arrow type | Arrow at source end |
| `endFill` | `0`, `1` | Fill end arrow |
| `startFill` | `0`, `1` | Fill start arrow |
| `endSize` | number | End arrow size |
| `startSize` | number | Start arrow size |

### Arrow Types

| Value | Description |
|-------|-------------|
| `none` | No arrow |
| `classic` | Classic arrow |
| `classicThin` | Thin classic arrow |
| `block` | Block arrow |
| `blockThin` | Thin block arrow |
| `open` | Open arrow |
| `openThin` | Thin open arrow |
| `oval` | Oval/circle |
| `diamond` | Diamond |
| `diamondThin` | Thin diamond |
| `box` | Box/square |
| `halfCircle` | Half circle |
| `dash` | Dash |
| `cross` | Cross |
| `circlePlus` | Circle with plus |
| `circle` | Circle |
| `ERone` | ER diagram "one" |
| `ERmandOne` | ER "mandatory one" |
| `ERmany` | ER "many" |
| `ERoneToMany` | ER "one to many" |
| `ERzeroToOne` | ER "zero to one" |
| `ERzeroToMany` | ER "zero to many" |

### Edge Routing

| Property | Values | Description |
|----------|--------|-------------|
| `edgeStyle` | style name | Edge routing algorithm |
| `curved` | `0`, `1` | Curved edges |
| `rounded` | `0`, `1` | Rounded corners |
| `orthogonal` | `0`, `1` | Orthogonal routing |
| `jettySize` | `auto`, number | Connector stub length |
| `sourcePortConstraint` | direction | Source exit direction |
| `targetPortConstraint` | direction | Target entry direction |

### Edge Style Values

| Value | Description |
|-------|-------------|
| `none` | Straight line |
| `orthogonalEdgeStyle` | Right-angle connectors |
| `elbowEdgeStyle` | Single elbow |
| `entityRelationEdgeStyle` | ER diagram style |
| `segmentEdgeStyle` | Segmented |
| `isometricEdgeStyle` | Isometric projection |

### Port Constraints

| Value | Description |
|-------|-------------|
| `north` | Top |
| `south` | Bottom |
| `east` | Right |
| `west` | Left |

### Examples

```
endArrow=classic;startArrow=none;
edgeStyle=orthogonalEdgeStyle;rounded=1;
curved=1;endArrow=blockThin;endFill=1;
```

## Container/Group Styles

| Property | Values | Description |
|----------|--------|-------------|
| `container` | `0`, `1` | Is a container |
| `collapsible` | `0`, `1` | Can be collapsed |
| `childLayout` | layout name | Auto-layout for children |
| `recursiveResize` | `0`, `1` | Resize with parent |
| `expand` | `0`, `1` | Expanded state |
| `swimlaneFillColor` | `#RRGGBB` | Swimlane body color |
| `swimlaneLine` | `0`, `1` | Show swimlane divider |
| `startSize` | number | Header height |
| `horizontalStack` | `0`, `1` | Stack horizontal |

## Image Styles

| Property | Values | Description |
|----------|--------|-------------|
| `image` | URL/path | Image source |
| `imageWidth` | number | Image width |
| `imageHeight` | number | Image height |
| `imageBackground` | `#RRGGBB` | Image background |
| `imageBorder` | `#RRGGBB` | Image border |
| `imageAlign` | `left`, `center`, `right` | Image alignment |
| `imageVerticalAlign` | `top`, `middle`, `bottom` | Vertical image alignment |
| `aspect` | `fixed` | Maintain aspect ratio |

### Examples

```
shape=image;image=img/lib/mscae/VirtualMachine.svg;
image=data:image/svg+xml,...;aspect=fixed;
```

## Miscellaneous Styles

| Property | Values | Description |
|----------|--------|-------------|
| `resizable` | `0`, `1` | Can be resized |
| `movable` | `0`, `1` | Can be moved |
| `rotatable` | `0`, `1` | Can be rotated |
| `deletable` | `0`, `1` | Can be deleted |
| `editable` | `0`, `1` | Label can be edited |
| `locked` | `0`, `1` | Locked (no editing) |
| `bendable` | `0`, `1` | Edge can bend |
| `cloneable` | `0`, `1` | Can be cloned |
| `foldable` | `0`, `1` | Can be folded |
| `pointerEvents` | `0`, `1` | Respond to pointer |
| `rotation` | degrees | Rotation angle |
| `direction` | `north`, `south`, `east`, `west` | Shape direction |
| `flipH` | `0`, `1` | Horizontal flip |
| `flipV` | `0`, `1` | Vertical flip |
| `glass` | `0`, `1` | Glass effect |
| `shadow` | `0`, `1` | Drop shadow |
| `sketch` | `0`, `1` | Hand-drawn style |
| `comic` | `0`, `1` | Comic/rough style |

## Default Styles

The default styles applied to new cells:

### Default Vertex Style
```
shape=rectangle;whiteSpace=wrap;html=1;
```

### Default Edge Style
```
edgeStyle=none;endArrow=classic;html=1;
```

## Creating Custom Styles

Register a named style in mxStylesheet:

```javascript
var style = {};
style[mxConstants.STYLE_SHAPE] = mxConstants.SHAPE_RECTANGLE;
style[mxConstants.STYLE_OPACITY] = 50;
style[mxConstants.STYLE_FONTCOLOR] = '#774400';
style[mxConstants.STYLE_FILLCOLOR] = '#dae8fc';
style[mxConstants.STYLE_STROKECOLOR] = '#6c8ebf';
graph.getStylesheet().putCellStyle('myCustomStyle', style);
```

Use in XML:
```xml
<mxCell style="myCustomStyle;fontSize=14;" .../>
```

## See Also

- [Draw.io Format Reference](format-reference.md)
- [mxCell API Reference](mxcell-api-reference.md)
- [mxConstants Reference](https://jgraph.github.io/mxgraph/docs/js-api/files/util/mxConstants-js.html)
