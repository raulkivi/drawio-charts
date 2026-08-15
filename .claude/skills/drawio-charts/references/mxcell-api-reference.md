# mxCell API Reference

> Source: [mxGraph JavaScript API](https://jgraph.github.io/mxgraph/docs/js-api/files/model/mxCell-js.html)

## Overview

Cells are the elements of the graph model. They represent the state of groups, vertices and edges in a graph. Every shape, connector, and container in a draw.io diagram is an `mxCell`.

## Constructor

```javascript
function mxCell(value, geometry, style)
```

**Parameters:**
- `value` - Optional object that represents the cell value (label or user object)
- `geometry` - Optional `mxGeometry` that specifies the geometry
- `style` - Optional formatted string that defines the style

## Properties

### Core Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `id` | string | null | Unique identifier for the cell |
| `value` | any | null | User object (label text or custom data) |
| `geometry` | mxGeometry | null | Position and size information |
| `style` | string | null | Style string: `[(stylename\|key=value);]` |

### Cell Type Flags

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `vertex` | boolean | false | True if cell is a vertex (shape) |
| `edge` | boolean | false | True if cell is an edge (connector) |
| `connectable` | boolean | true | Whether connections can be made to this cell |
| `visible` | boolean | true | Whether cell is visible |
| `collapsed` | boolean | false | Whether cell is collapsed (for groups) |

### Relationship Properties

| Property | Type | Description |
|----------|------|-------------|
| `parent` | mxCell | Reference to the parent cell |
| `source` | mxCell | For edges: reference to source terminal |
| `target` | mxCell | For edges: reference to target terminal |
| `children` | array | Array of child cells |
| `edges` | array | Array of connected edges |

## Methods

### Identification

```javascript
cell.getId()           // Returns the cell ID as string
cell.setId(id)         // Sets the cell ID
```

### Value (Label/User Object)

```javascript
cell.getValue()              // Returns the user object
cell.setValue(value)         // Sets the user object
cell.valueChanged(newValue)  // Changes value after edit, returns previous
```

### Geometry

```javascript
cell.getGeometry()           // Returns the mxGeometry
cell.setGeometry(geometry)   // Sets the mxGeometry
```

### Style

```javascript
cell.getStyle()        // Returns style string
cell.setStyle(style)   // Sets style string
```

### Type Checking

```javascript
cell.isVertex()        // Returns true if vertex
cell.setVertex(bool)   // Set vertex flag (only at construction)
cell.isEdge()          // Returns true if edge
cell.setEdge(bool)     // Set edge flag (only at construction)
cell.isConnectable()   // Returns true if connectable
cell.setConnectable(bool)
cell.isVisible()       // Returns true if visible
cell.setVisible(bool)
cell.isCollapsed()     // Returns true if collapsed
cell.setCollapsed(bool)
```

### Parent/Child Relationships

```javascript
cell.getParent()             // Returns parent cell
cell.setParent(parent)       // Sets parent cell
cell.getChildCount()         // Returns number of children
cell.getChildAt(index)       // Returns child at index
cell.getIndex(child)         // Returns index of child
cell.insert(child, index)    // Inserts child at index
cell.remove(index)           // Removes child at index
cell.removeFromParent()      // Removes cell from its parent
```

### Edge Connections (Terminals)

```javascript
cell.getTerminal(isSource)           // Returns source or target terminal
cell.setTerminal(terminal, isSource) // Sets source or target terminal
cell.getEdgeCount()                  // Returns number of connected edges
cell.getEdgeAt(index)                // Returns edge at index
cell.getEdgeIndex(edge)              // Returns index of edge
cell.insertEdge(edge, isOutgoing)    // Inserts edge
cell.removeEdge(edge, isOutgoing)    // Removes edge
cell.removeFromTerminal(isSource)    // Removes from source/target
```

### Custom Attributes (XML User Objects)

```javascript
cell.hasAttribute(name)              // True if XML node has attribute
cell.getAttribute(name, defaultVal)  // Get attribute value
cell.setAttribute(name, value)       // Set attribute value
```

### Cloning

```javascript
cell.clone()       // Returns clone of cell
cell.cloneValue()  // Returns clone of user object
```

## XML Representation

In draw.io files, cells are serialized as:

```xml
<!-- Vertex (shape) -->
<mxCell id="2" value="Hello" style="rounded=1;fillColor=#dae8fc;" 
        parent="1" vertex="1">
  <mxGeometry x="120" y="100" width="80" height="40" as="geometry"/>
</mxCell>

<!-- Edge (connector) -->
<mxCell id="3" value="" style="endArrow=classic;" 
        parent="1" source="2" target="4" edge="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

## Custom Attributes Example

For complex data, use an XML node as the cell value:

```javascript
var doc = mxUtils.createXmlDocument();
var node = doc.createElement('MyNode');
node.setAttribute('label', 'MyLabel');
node.setAttribute('attribute1', 'value1');
graph.insertVertex(graph.getDefaultParent(), null, node, 40, 40, 80, 30);
```

To make labels work with custom XML values, override:

```javascript
graph.convertValueToString = function(cell) {
  if (mxUtils.isNode(cell.value)) {
    return cell.getAttribute('label', '');
  }
  return cell.value;
};
```

## Special Cell IDs

| ID | Description |
|----|-------------|
| `"0"` | Root cell (invisible, parent of all) |
| `"1"` | Default layer (first child of root, parent for diagram cells) |

## See Also

- [mxGeometry API Reference](mxgeometry-api-reference.md)
- [Draw.io Format Reference](format-reference.md)
- [mxGraph Manual](https://jgraph.github.io/mxgraph/docs/manual.html)
