# mxGeometry API Reference

> Source: [mxGraph JavaScript API](https://jgraph.github.io/mxgraph/docs/js-api/files/model/mxGeometry-js.html)

## Overview

`mxGeometry` extends `mxRectangle` to represent the geometry of a cell. For vertices, it stores x, y, width, and height. For edges, it stores optional terminal points and control points (waypoints).

## Constructor

```javascript
function mxGeometry(x, y, width, height)
```

**Parameters:**
- `x` - X coordinate (or relative position for edges)
- `y` - Y coordinate (or relative position for edges)  
- `width` - Width of the cell
- `height` - Height of the cell

## Properties

### Position & Size (Inherited from mxRectangle)

| Property | Type | Description |
|----------|------|-------------|
| `x` | number | X coordinate of top-left corner |
| `y` | number | Y coordinate of top-left corner |
| `width` | number | Width of the geometry |
| `height` | number | Height of the geometry |

### Edge-Specific Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `sourcePoint` | mxPoint | null | Source point for unconnected edges |
| `targetPoint` | mxPoint | null | Target point for unconnected edges |
| `points` | mxPoint[] | null | Control points (waypoints) along the edge |

### Positioning Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `relative` | boolean | false | If true, coordinates are relative |
| `offset` | mxPoint | null | Offset from calculated position |
| `alternateBounds` | mxRectangle | null | Alternate bounds for collapsed state |

### Configuration

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `TRANSLATE_CONTROL_POINTS` | boolean | true | Whether to translate control points |

## Methods

### Terminal Points (for Edges)

```javascript
geometry.getTerminalPoint(isSource)        // Returns source or target point
geometry.setTerminalPoint(point, isSource) // Sets source or target point
```

### Transformations

```javascript
geometry.swap()                    // Swap bounds with alternateBounds
geometry.rotate(angle, center)     // Rotate around center point
geometry.translate(dx, dy)         // Move by offset
geometry.scale(sx, sy, fixedAspect) // Scale by factors
```

### Comparison

```javascript
geometry.equals(obj)  // Returns true if geometries are equal
```

## Coordinate Systems

### Absolute Positioning (Vertices)

For vertices with `relative=false` (default):
- `x`, `y` are absolute coordinates relative to parent cell
- Position is from top-left corner of parent to top-left of cell

```xml
<mxGeometry x="100" y="50" width="120" height="60" as="geometry"/>
```

### Relative Positioning (Vertices)

For vertices with `relative=true`:
- `x`, `y` are proportions of parent size (0 to 1)
- (0,0) = parent origin, (1,1) = parent bottom-right
- Useful for keeping children positioned relative to parent size

```xml
<mxGeometry x="0.5" y="0.5" width="40" height="40" relative="1" as="geometry"/>
```

### Edge Label Positioning

For edges, geometry controls the label position:

**Non-relative (absolute):**
- `x`, `y` are absolute offset from graph origin

**Relative (default for edges):**
- `x` = position along edge: -1 (source) to 1 (target), 0 = center
- `y` = perpendicular offset in pixels from edge
- `offset` = additional absolute offset

```xml
<!-- Label at center of edge -->
<mxGeometry relative="1" as="geometry"/>

<!-- Label 1/4 from source, 10px below edge -->
<mxGeometry x="-0.5" y="10" relative="1" as="geometry"/>
```

## Edge Control Points

Control points define the path of an edge:

```xml
<mxGeometry relative="1" as="geometry">
  <Array as="points">
    <mxPoint x="200" y="150"/>
    <mxPoint x="200" y="250"/>
  </Array>
</mxGeometry>
```

For unconnected edges (no source/target vertex):

```javascript
geometry.setTerminalPoint(new mxPoint(x1, y1), true);   // source
geometry.points = [new mxPoint(x2, y2)];                // waypoints
geometry.setTerminalPoint(new mxPoint(x3, y3), false);  // target
```

## Offsets

The `offset` property has different meanings:

| Context | Offset Meaning |
|---------|----------------|
| Edge labels | Absolute offset from calculated position |
| Relative vertex | Absolute offset from relative position |
| Absolute vertex | Offset for label inside the vertex |

```xml
<mxGeometry x="100" y="100" width="80" height="40" as="geometry">
  <mxPoint x="10" y="5" as="offset"/>
</mxGeometry>
```

## Alternate Bounds (for Collapsible Groups)

Groups can have different bounds when collapsed vs expanded:

```javascript
// Store alternate bounds
geometry.alternateBounds = new mxRectangle(x, y, 100, 30);

// Swap between normal and alternate
geometry.swap();
```

## XML Representation

### Vertex Geometry

```xml
<mxGeometry x="120" y="80" width="100" height="60" as="geometry"/>
```

### Relative Vertex Geometry

```xml
<mxGeometry x="0.5" y="0" width="20" height="20" relative="1" as="geometry">
  <mxPoint x="-10" y="-10" as="offset"/>
</mxGeometry>
```

### Edge Geometry with Waypoints

```xml
<mxGeometry relative="1" as="geometry">
  <mxPoint x="150" y="100" as="sourcePoint"/>
  <mxPoint x="300" y="200" as="targetPoint"/>
  <Array as="points">
    <mxPoint x="200" y="100"/>
    <mxPoint x="200" y="200"/>
  </Array>
</mxGeometry>
```

## Common Patterns

### Center a Child in Parent

```xml
<mxGeometry x="0.5" y="0.5" width="40" height="40" relative="1" as="geometry">
  <mxPoint x="-20" y="-20" as="offset"/>
</mxGeometry>
```

### Position Edge Label Below Edge

```xml
<mxGeometry x="0" y="20" relative="1" as="geometry"/>
```

### Orthogonal Edge with Waypoints

```xml
<mxGeometry relative="1" as="geometry">
  <Array as="points">
    <mxPoint x="200" y="120"/>
    <mxPoint x="200" y="200"/>
  </Array>
</mxGeometry>
```

## See Also

- [mxCell API Reference](mxcell-api-reference.md)
- [Draw.io Format Reference](format-reference.md)
- [mxPoint](https://jgraph.github.io/mxgraph/docs/js-api/files/util/mxPoint-js.html)
- [mxRectangle](https://jgraph.github.io/mxgraph/docs/js-api/files/util/mxRectangle-js.html)
