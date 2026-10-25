# Mermaid → graph spec mapping

How to turn a Mermaid diagram into the JSON graph spec that `scripts/layout_drawio.py` lays out. You write the spec by reading the Mermaid; the scripts do the layout, styling and draw.io XML. Worked pairs (`.mmd` source plus `.json` spec) for every type are in `assets/examples/mermaid/`.

## Contents

- [Spec basics](#spec-basics)
- [Flowchart](#flowchart)
- [State diagram](#state-diagram)
- [Class diagram](#class-diagram)
- [ER diagram](#er-diagram)
- [Sequence diagram](#sequence-diagram)
- [Not converted](#not-converted)
- [Checking the conversion](#checking-the-conversion)

## Spec basics

```json
{
  "type": "flowchart | state | class | er | sequence",
  "title": "optional page name",
  "direction": "TD | TB | BT | LR | RL",
  "nodes":   [{"id": "A", "label": "Text", "shape": "rect", "class": "name", "style": {"fill": "#hex"}}],
  "edges":   [{"from": "A", "to": "B", "label": "", "line": "solid", "head": "arrow", "tail": "none",
               "fromLabel": "", "toLabel": ""}],
  "groups":  [{"id": "g", "label": "Group", "members": ["A"], "groups": []}],
  "classes": {"name": {"fill": "#hex", "stroke": "#hex", "color": "#hex", "stroke-width": "2px"}}
}
```

- Keep Mermaid's node ids, so the spec can be checked against the source. A label defaults to the id.
- `line`: `solid`, `dotted`, `thick` or `invisible`.
- `head`/`tail` markers: `none`, `arrow`, `open`, `triangle` (hollow), `diamond` (filled), `odiamond` (hollow), `circle`, `cross`, `one`, `zero_or_one`, `one_or_more`, `zero_or_more`.
- A node belongs to at most one group, and groups nest through `groups`. An edge may start or end on a group id.
- `classes` and per-node `style` take Mermaid's CSS names: `fill`, `stroke`, `color`, `stroke-width`, `stroke-dasharray`, `font-weight`. Other properties are dropped.
- Labels are plain text. Write `\n` for a line break where Mermaid has `<br>`.
- `layout_drawio.py` rejects a spec with unknown ids, shapes or markers, and the error says where. Fix the spec and rerun.

## Flowchart

`flowchart` / `graph` → `"type": "flowchart"`, and `TD`/`TB`/`BT`/`LR`/`RL` → `direction`.

| Mermaid | `shape` |
|---|---|
| `A[text]` | `rect` |
| `A(text)` | `rounded` |
| `A([text])` | `stadium` |
| `A[[text]]` | `subroutine` |
| `A[(text)]` | `cylinder` |
| `A((text))` | `circle` |
| `A(((text)))` | `doublecircle` |
| `A{text}` | `rhombus` |
| `A{{text}}` | `hexagon` |
| `A[/text/]`, `A[\text\]` | `parallelogram` |
| `A[/text\]`, `A[\text/]` | `trapezoid` |
| `A>text]` | `asymmetric` |
| `A@{ shape: … }` (v11 shapes) | the closest of the above |

| Mermaid edge | Spec |
|---|---|
| `A --> B` | defaults (`solid`, `head: arrow`) |
| `A --- B` | `head: none` |
| `A -.-> B` / `A -.- B` | `line: dotted` (+ `head: none` for `-.-`) |
| `A ==> B` / `A === B` | `line: thick` |
| `A ~~~ B` | `line: invisible` (keeps layout, draws nothing) |
| `A --o B` / `A --x B` | `head: circle` / `head: cross` |
| `A <--> B` | `head: arrow`, `tail: arrow` |
| `A -->\|text\| B`, `A -- text --> B` | `label: "text"` |
| `A --> B --> C` | one edge per hop |
| `A & B --> C & D` | one edge per pair (4 here) |

- **Subgraphs:** `subgraph id [Title] … end` becomes a group with id `id`, label `Title` and the nodes defined or first used inside it as `members`. Nested subgraphs become nested `groups`. A `direction` line inside a subgraph is ignored, because the whole diagram uses one direction.
- **Styling:** `classDef name fill:…,stroke:…` becomes `classes.name`. `class A,B name` and `A:::name` set `"class": "name"` on those nodes. `style A fill:…` becomes that node's `style`. `linkStyle` is dropped.
- **Dropped:** `click`, `callback` and markdown-string formatting. Keep the text, lose the formatting.

## State diagram

`stateDiagram` / `stateDiagram-v2` → `"type": "state"`, and `direction` as in Mermaid (default `TD`).

- Each `[*]` becomes its own node: `{"id": "_start", "shape": "start"}` where it is a source and `{"id": "_end", "shape": "end"}` where it is a target. Inside a composite state, use fresh ids like `_published_start`. Ids starting with `_` are understood to have no counterpart in the Mermaid.
- A state becomes a node with `shape: rounded`. `state "Long name" as S` gives id `S` and label `Long name`.
- Transitions `A --> B : event` become edges with `label: "event"`.
- A composite `state X { … }` becomes a group `X`. Transitions to or from `X` itself use the group id.
- `<<choice>>` becomes `rhombus`, and `<<fork>>`/`<<join>>` become `fork`.
- A note becomes a `note` node with a `line: dotted, head: none` edge to its state.
- Concurrency separators (`--`) are dropped. Put the regions in one group.

## Class diagram

`classDiagram` → `"type": "class"`, default `TD`.

- Each class becomes `{"id": "Name", "shape": "class", "attributes": [...], "methods": [...]}`.
  - Members are kept as Mermaid writes them (`+id: int`, `-total() decimal`). Lines with `(` are methods.
  - `<<interface>>` and other annotations go in `stereotype` (without the angle brackets).
  - A class that only appears in a relation still gets a node, with empty lists.
  - Generics `List~int~` become `List<int>` (it is escaped for you).
- Relations keep Mermaid's left-to-right order. The left class is `from`, and its end is the `tail`. With that convention, parents and owners are laid out above children.

| Mermaid | `line` | `tail` (left end) | `head` (right end) |
|---|---|---|---|
| `A <\|-- B` inheritance | solid | `triangle` | `none` |
| `A <\|.. B` realization | dotted | `triangle` | `none` |
| `A *-- B` composition | solid | `diamond` | `none` |
| `A o-- B` aggregation | solid | `odiamond` | `none` |
| `A --> B` association | solid | `none` | `arrow` |
| `A ..> B` dependency | dotted | `none` | `open` |
| `A -- B` / `A .. B` link | solid / dotted | `none` | `none` |

- If Mermaid writes it the other way round (`B --|> A`), swap the ends to keep the parent first.
- Cardinality `A "1" --> "*" B` becomes `fromLabel: "1"` and `toLabel: "*"`.
- `: label` after a relation becomes `label`.

## ER diagram

`erDiagram` → `"type": "er"`. Use `direction: "LR"` for up to about 6 entities in a chain, otherwise `TD`.

- Each entity becomes `{"id": "NAME", "shape": "entity", "attributes": [{"name": "id", "type": "int", "key": "PK"}]}`.
  - Mermaid writes `type name key "comment"`. `key` may be `PK`, `FK`, `UK` or a combination like `"PK, FK"`. Comments are dropped.
  - An entity with no attribute block still gets a node.
- In a relationship `A ||--o{ B : label`, the left marker belongs to A (`tail`) and the right marker to B (`head`):

| Mermaid (left / right) | Marker |
|---|---|
| `\|\|` / `\|\|` | `one` |
| `\|o` / `o\|` | `zero_or_one` |
| `}\|` / `\|{` | `one_or_more` |
| `}o` / `o{` | `zero_or_more` |

- `--` is identifying (`line: solid`) and `..` is non-identifying (`line: dotted`). Quoted labels lose their quotes.

## Sequence diagram

`sequenceDiagram` → `"type": "sequence"`, using `participants` and `items` instead of nodes and edges:

```json
{
  "type": "sequence",
  "participants": [{"id": "U", "label": "User", "kind": "actor"}, {"id": "API"}],
  "items": [
    {"message": {"from": "U", "to": "API", "label": "POST /orders", "line": "solid", "head": "arrow", "activate": true}},
    {"note": {"over": ["U", "API"], "position": "over", "text": "…"}},
    {"activate": "API"}, {"deactivate": "API"},
    {"frame": {"kind": "alt", "sections": [{"label": "ok", "items": []}, {"label": "error", "items": []}]}}
  ]
}
```

- **Participants:** `participant A as Label` / `actor A as Label` set `id`, `label` and `kind`, in the order Mermaid shows them. That is the declaration order first, then first use.
- **Messages:** list them in order.

| Mermaid arrow | `line` | `head` |
|---|---|---|
| `->>` / `-->>` | solid / dotted | `arrow` |
| `->` / `-->` | solid / dotted | `none` |
| `-x` / `--x` | solid / dotted | `cross` |
| `-)` / `--)` | solid / dotted | `open` |
| `<<->>` / `<<-->>` | solid / dotted | `arrow` (add a reply message if needed) |

- **Activations:** `A->>+B` sets `"activate": true` (B becomes active), and `B-->>-A` sets `"deactivate": true` (B stops). Standalone `activate X` / `deactivate X` lines are items.
- **Notes:** `Note left of A`, `right of A` and `over A,B` become `note` items with `position` `left of`, `right of` or `over`.
- **Frames:** `loop`, `alt`/`else`, `opt`, `par`/`and`, `critical`/`option`, `break` and `rect` become `frame` items. Each `else`/`and`/`option` starts a new section. Frames nest.
- **Dropped:** `autonumber`. Number the labels yourself ("1. Login") if the numbers matter. `box` groupings, `create`/`destroy` and `links` are also dropped.

## Not converted

`gantt`, `pie`, `gitGraph`, `mindmap`, `timeline`, `journey`, `quadrantChart`, `xychart`, `sankey`, `block`, `C4*`, `requirementDiagram` and `architecture` have no graph-spec form. Leave those blocks as Mermaid and list them in your summary. `replace_mermaid.py` marks them `unsupported` and never replaces them.

## Checking the conversion

Before writing the image, compare the spec with the Mermaid:

- Every node id or participant from the Mermaid is in the spec (ids starting with `_` excepted).
- The number of edges or messages matches. Remember to expand chains and `&`.
- Every label in the Mermaid appears in the spec: node text, edge labels, notes, frame conditions.
- Subgraph and composite-state membership matches.

`layout_drawio.py` checks the spec's structure. Only you can check it says the same thing as the Mermaid.
