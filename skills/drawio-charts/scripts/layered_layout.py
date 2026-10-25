"""Layered ("Sugiyama-style") layout for one level of a directed graph.

Pure geometry: it knows box sizes and edges, nothing about draw.io. Steps:
  1. break cycles by reversing DFS back edges
  2. rank nodes by longest path from the sources
  3. split edges that skip ranks with dummy nodes (they become waypoints)
  4. order each rank with barycentre sweeps, keeping the fewest crossings
  5. place nodes on the cross axis, pulling each towards its neighbours
  6. map rank/cross axes to x/y for the requested direction
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable
from dataclasses import dataclass

Point = tuple[float, float]
DUMMY_BREADTH = 20.0
SWEEPS = 24
PLACEMENT_PASSES = 8
DUMMY_PULL = 0.3


@dataclass(frozen=True)
class LayoutResult:
    positions: dict[str, Point]          # top-left corner of each node
    size: Point                          # width, height of the whole level
    edge_points: dict[Hashable, list[Point]]


def layered_layout(
    nodes: Iterable[tuple[str, float, float]],
    edges: Iterable[tuple[Hashable, str, str]],
    direction: str = "TD",
    node_gap: float = 40,
    rank_gap: float = 60,
) -> LayoutResult:
    nodes = list(nodes)
    edges = list(edges)
    order = {node_id: i for i, (node_id, _, _) in enumerate(nodes)}
    horizontal = direction in ("LR", "RL")
    # breadth runs across a rank, thickness along the flow
    breadth = {n: (h if horizontal else w) for n, w, h in nodes}
    thickness = {n: (w if horizontal else h) for n, w, h in nodes}

    links = [(key, u, v) for key, u, v in edges if u != v]
    reversed_keys = _back_edges(order, links)
    flow = [(key, v, u) if key in reversed_keys else (key, u, v) for key, u, v in links]
    rank = _longest_path_ranks(order, flow)

    chains: dict[Hashable, list[str]] = {}
    proper: list[tuple[str, str]] = []
    for key, u, v in flow:
        chain = [u]
        for step in range(rank[u] + 1, rank[v]):
            dummy = f"\0{key!r}:{step}"
            rank[dummy] = step
            breadth[dummy], thickness[dummy] = DUMMY_BREADTH, 0.0
            chain.append(dummy)
        chain.append(v)
        proper.extend(zip(chain, chain[1:]))
        chains[key] = chain[1:-1] if key not in reversed_keys else chain[-2:0:-1]

    layers = _initial_layers(order, rank, proper)
    layers = _reduce_crossings(layers, proper)
    cross = _place_cross_axis(layers, proper, breadth, node_gap)

    rank_count = len(layers)
    band = [max((thickness[n] for n in layers[r]), default=0.0) for r in range(rank_count)]
    band_start, offset = [], 0.0
    for r in range(rank_count):
        band_start.append(offset)
        offset += band[r] + (rank_gap if r < rank_count - 1 else 0)
    total_rank = offset

    left = min(cross[n] for n in cross)
    total_breadth = max(cross[n] + breadth[n] for n in cross) - left

    def place(node: str) -> Point:
        along = band_start[rank[node]] + (band[rank[node]] - thickness[node]) / 2
        if direction in ("BT", "RL"):
            along = total_rank - along - thickness[node]
        across = cross[node] - left
        return (along, across) if horizontal else (across, along)

    positions = {n: place(n) for n, _, _ in nodes}
    edge_points: dict[Hashable, list[Point]] = {key: [] for key, _, _ in edges}
    for key, chain in chains.items():
        points = []
        for dummy in chain:
            x, y = place(dummy)
            points.append((x + DUMMY_BREADTH / 2, y) if not horizontal else (x, y + DUMMY_BREADTH / 2))
        edge_points[key] = points
    size = (total_rank, total_breadth) if horizontal else (total_breadth, total_rank)
    return LayoutResult(positions, size, edge_points)


def count_crossings(layers: list[list[str]], edges: Iterable[tuple[str, str]]) -> int:
    position = {n: (r, i) for r, layer in enumerate(layers) for i, n in enumerate(layer)}
    by_gap: dict[int, list[tuple[int, int]]] = {}
    for u, v in edges:
        (ru, iu), (rv, iv) = position[u], position[v]
        if abs(ru - rv) != 1:
            continue
        if ru > rv:
            (ru, iu), (rv, iv) = (rv, iv), (ru, iu)
        by_gap.setdefault(ru, []).append((iu, iv))
    total = 0
    for pairs in by_gap.values():
        for i, (a1, b1) in enumerate(pairs):
            for a2, b2 in pairs[i + 1:]:
                if (a1 - a2) * (b1 - b2) < 0:
                    total += 1
    return total


def _back_edges(order: dict[str, int], links: list[tuple[Hashable, str, str]]) -> set[Hashable]:
    outgoing: dict[str, list[tuple[Hashable, str]]] = {n: [] for n in order}
    for key, u, v in links:
        outgoing[u].append((key, v))
    state = dict.fromkeys(order, 0)  # 0 new, 1 on stack, 2 done
    back = set()
    for root in order:
        if state[root]:
            continue
        state[root] = 1
        stack = [(root, iter(outgoing[root]))]
        while stack:
            node, children = stack[-1]
            for key, child in children:
                if state[child] == 1:
                    back.add(key)
                elif state[child] == 0:
                    state[child] = 1
                    stack.append((child, iter(outgoing[child])))
                    break
            else:
                state[node] = 2
                stack.pop()
    return back


def _longest_path_ranks(order: dict[str, int], flow: list[tuple[Hashable, str, str]]) -> dict[str, int]:
    incoming = dict.fromkeys(order, 0)
    successors: dict[str, list[str]] = {n: [] for n in order}
    for _, u, v in flow:
        incoming[v] += 1
        successors[u].append(v)
    rank = dict.fromkeys(order, 0)
    ready = sorted((n for n in order if incoming[n] == 0), key=order.get)
    while ready:
        node = ready.pop(0)
        for child in successors[node]:
            rank[child] = max(rank[child], rank[node] + 1)
            incoming[child] -= 1
            if incoming[child] == 0:
                ready.append(child)
                ready.sort(key=order.get)
    return rank


def _initial_layers(order: dict[str, int], rank: dict[str, int], proper: list[tuple[str, str]]) -> list[list[str]]:
    """Order each rank by a depth-first walk, which keeps components together."""
    successors: dict[str, list[str]] = {n: [] for n in rank}
    has_parent = set()
    for u, v in proper:
        successors[u].append(v)
        has_parent.add(v)
    visit_index: dict[str, int] = {}
    roots = [n for n in sorted(order, key=order.get) if n not in has_parent] + sorted(order, key=order.get)
    for root in roots:
        stack = [root]
        while stack:
            node = stack.pop()
            if node in visit_index:
                continue
            visit_index[node] = len(visit_index)
            stack.extend(reversed(successors[node]))
    layers: list[list[str]] = [[] for _ in range(max(rank.values(), default=-1) + 1)]
    for node in sorted(rank, key=lambda n: visit_index.get(n, len(visit_index))):
        layers[rank[node]].append(node)
    return layers


def _reduce_crossings(layers: list[list[str]], proper: list[tuple[str, str]]) -> list[list[str]]:
    up: dict[str, list[str]] = {n: [] for layer in layers for n in layer}
    down: dict[str, list[str]] = {n: [] for layer in layers for n in layer}
    for u, v in proper:
        down[u].append(v)
        up[v].append(u)
    best, best_crossings = [list(layer) for layer in layers], count_crossings(layers, proper)
    current = [list(layer) for layer in layers]
    for sweep in range(SWEEPS):
        downward = sweep % 2 == 0
        indices = range(1, len(current)) if downward else range(len(current) - 2, -1, -1)
        for r in indices:
            fixed = current[r - 1] if downward else current[r + 1]
            neighbours = up if downward else down
            where = {n: i for i, n in enumerate(fixed)}

            def barycentre(item: tuple[int, str]) -> float:
                index, node = item
                linked = [where[m] for m in neighbours[node] if m in where]
                return sum(linked) / len(linked) if linked else float(index)

            current[r] = [n for _, n in sorted(enumerate(current[r]), key=lambda item: (barycentre(item), item[0]))]
        crossings = count_crossings(current, proper)
        if crossings < best_crossings:
            best, best_crossings = [list(layer) for layer in current], crossings
        if best_crossings == 0:
            break
    return best


def _place_cross_axis(layers: list[list[str]], proper: list[tuple[str, str]],
                      breadth: dict[str, float], node_gap: float) -> dict[str, float]:
    """Left edge of every node on the cross axis."""
    up: dict[str, list[str]] = {n: [] for layer in layers for n in layer}
    down: dict[str, list[str]] = {n: [] for layer in layers for n in layer}
    for u, v in proper:
        down[u].append(v)
        up[v].append(u)

    def gap(a: str, b: str) -> float:
        return node_gap if not (a.startswith("\0") or b.startswith("\0")) else node_gap / 2

    centre: dict[str, float] = {}
    for layer in layers:
        x = 0.0
        for i, node in enumerate(layer):
            if i:
                x += gap(layer[i - 1], node)
            centre[node] = x + breadth[node] / 2
            x += breadth[node]
        shift = x / 2
        for node in layer:
            centre[node] -= shift

    for p in range(PLACEMENT_PASSES):
        neighbours = up if p % 2 == 0 else down
        for layer in layers:
            desired = []
            for node in layer:
                # real neighbours pull harder than the dummy points of long edges
                weights = [(centre[m], DUMMY_PULL if m.startswith("\0") else 1.0) for m in neighbours[node]]
                total = sum(w for _, w in weights)
                desired.append(sum(c * w for c, w in weights) / total if weights else centre[node])
            pushed_right, pushed_left = [], []
            for i, node in enumerate(layer):
                start = desired[i] - breadth[node] / 2
                if i:
                    prev = layer[i - 1]
                    start = max(start, pushed_right[-1] + breadth[prev] + gap(prev, node))
                pushed_right.append(start)
            for i in range(len(layer) - 1, -1, -1):
                node = layer[i]
                start = desired[i] - breadth[node] / 2
                if i < len(layer) - 1:
                    nxt = layer[i + 1]
                    start = min(start, pushed_left[0] - gap(node, nxt) - breadth[node])
                pushed_left.insert(0, start)
            for i, node in enumerate(layer):
                centre[node] = (pushed_right[i] + pushed_left[i]) / 2 + breadth[node] / 2
    return {n: centre[n] - breadth[n] / 2 for n in centre}
