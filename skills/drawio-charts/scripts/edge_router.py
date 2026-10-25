"""Orthogonal edge geometry shared by the layout and the SVG renderer.

default_route() is the simple route the renderer draws (leave the side
facing the other end, cross over halfway). When that route would run
through another node, route_around() finds waypoints with a grid search
that avoids obstacles and charges extra for each bend.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass

Point = tuple[float, float]
GRID = 10
CLEARANCE = 10
TURN_COST = 6
MAX_CELLS = 250_000


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def inflate(self, by: float) -> Rect:
        return Rect(self.x - by, self.y - by, self.w + 2 * by, self.h + 2 * by)

    def contains(self, point: Point) -> bool:
        return self.x < point[0] < self.x + self.w and self.y < point[1] < self.y + self.h


def side_anchor(box: Rect, towards: Point | None, horizontal_only: bool = False,
                slot: float = 0.5) -> tuple[Point, str]:
    """Point on the side of box facing `towards`; slot runs 0..1 along that side."""
    if towards is None:
        return (box.x + box.w * slot, box.y + box.h), "bottom"
    dx, dy = towards[0] - box.cx, towards[1] - box.cy
    if not horizontal_only and abs(dy) * box.w >= abs(dx) * box.h:
        x = box.x + box.w * slot
        return ((x, box.y + box.h), "bottom") if dy >= 0 else ((x, box.y), "top")
    y = box.y + box.h * slot
    return ((box.x + box.w, y), "right") if dx >= 0 else ((box.x, y), "left")


def orthogonalise(points: list[Point], start_side: str | None, end_side: str | None) -> list[Point]:
    result = [points[0]]
    vertical = start_side in ("top", "bottom") if start_side else None
    for i, q in enumerate(points[1:], start=1):
        p = result[-1]
        last = i == len(points) - 1
        if abs(p[0] - q[0]) < 0.01 or abs(p[1] - q[1]) < 0.01:
            result.append(q)
            vertical = abs(p[0] - q[0]) < 0.01
            continue
        if vertical is None:
            vertical = abs(q[1] - p[1]) > abs(q[0] - p[0])
        end_vertical = end_side in ("top", "bottom") if (last and end_side) else None
        # Z shapes cross over halfway between the points, which in a layered layout is
        # the gap between ranks, so they stay clear of shapes. An L is only used to
        # meet an end that must be entered from the side the route isn't travelling.
        if vertical and end_vertical is not False:      # Z: down, across, down
            mid = (p[1] + q[1]) / 2
            result += [(p[0], mid), (q[0], mid)]
        elif not vertical and end_vertical is not True:  # Z: across, down, across
            mid = (p[0] + q[0]) / 2
            result += [(mid, p[1]), (mid, q[1])]
        elif vertical:                                   # L: down then across
            result.append((p[0], q[1]))
            vertical = False
        else:                                            # L: across then down
            result.append((q[0], p[1]))
            vertical = True
        result.append(q)
    return result


def default_route(source: Rect, target: Rect, waypoints: list[Point] = (),
                  horizontal_only: bool = False) -> list[Point]:
    waypoints = list(waypoints)
    start, start_side = side_anchor(source, waypoints[0] if waypoints else (target.cx, target.cy), horizontal_only)
    end, end_side = side_anchor(target, waypoints[-1] if waypoints else start, horizontal_only)
    return orthogonalise([start, *waypoints, end], start_side, end_side)


def route_crosses(points: list[Point], obstacles: list[Rect]) -> bool:
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        for r in obstacles:
            if (min(x1, x2) < r.x + r.w - 1 and max(x1, x2) > r.x + 1
                    and min(y1, y2) < r.y + r.h - 1 and max(y1, y2) > r.y + 1):
                return True
    return False


def route_around(source: Rect, target: Rect, obstacles: list[Rect]) -> list[Point]:
    """Waypoints (bend points) of an obstacle-free orthogonal route, or [] if none."""
    blocked = [o.inflate(CLEARANCE) for o in obstacles]
    every = [source, target, *blocked]
    left = min(r.x for r in every) - 4 * GRID
    top = min(r.y for r in every) - 4 * GRID
    right = max(r.x + r.w for r in every) + 4 * GRID
    bottom = max(r.y + r.h for r in every) + 4 * GRID
    cols, rows = int((right - left) / GRID) + 1, int((bottom - top) / GRID) + 1
    if cols * rows > MAX_CELLS:
        return []

    def point(c: int, r: int) -> Point:
        return (left + c * GRID, top + r * GRID)

    def free(c: int, r: int) -> bool:
        p = point(c, r)
        return not any(b.contains(p) for b in blocked)

    def cell(p: Point) -> tuple[int, int]:
        return round((p[0] - left) / GRID), round((p[1] - top) / GRID)

    start, goal = cell((source.cx, source.cy)), cell((target.cx, target.cy))
    inside_source = {cell_ for cell_ in _cells_in(source, cell)}
    inside_target = {cell_ for cell_ in _cells_in(target, cell)}
    steps = ((1, 0), (-1, 0), (0, 1), (0, -1))
    frontier = [(0, 0, start, -1)]
    best = {(start, -1): 0}
    came: dict[tuple, tuple] = {}
    while frontier:
        _, cost, (c, r), heading = heapq.heappop(frontier)
        if (c, r) == goal:
            return _bends(_walk_back(came, ((c, r), heading)), point, source, target)
        if cost > best.get(((c, r), heading), float("inf")):
            continue
        for d, (dc, dr) in enumerate(steps):
            nc, nr = c + dc, r + dr
            if not (0 <= nc < cols and 0 <= nr < rows):
                continue
            if (nc, nr) not in inside_source and (nc, nr) not in inside_target and not free(nc, nr):
                continue
            step = 1 + (TURN_COST if heading not in (-1, d) else 0)
            new = cost + step
            key = ((nc, nr), d)
            if new < best.get(key, float("inf")):
                best[key] = new
                came[key] = ((c, r), heading)
                estimate = abs(goal[0] - nc) + abs(goal[1] - nr)
                heapq.heappush(frontier, (new + estimate, new, (nc, nr), d))
    return []


def _cells_in(box: Rect, cell) -> list[tuple[int, int]]:
    (c0, r0), (c1, r1) = cell((box.x, box.y)), cell((box.x + box.w, box.y + box.h))
    return [(c, r) for c in range(c0, c1 + 1) for r in range(r0, r1 + 1)]


def _walk_back(came: dict, key: tuple) -> list[tuple[int, int]]:
    path = [key[0]]
    while key in came:
        key = came[key]
        path.append(key[0])
    return path[::-1]


def _bends(path: list[tuple[int, int]], point, source: Rect, target: Rect) -> list[Point]:
    """Corner points of the grid path, except those strictly inside an end box."""
    corners = []
    for prev, here, nxt in zip(path, path[1:], path[2:]):
        if (here[0] - prev[0], here[1] - prev[1]) != (nxt[0] - here[0], nxt[1] - here[1]):
            p = point(*here)
            if not source.contains(p) and not target.contains(p):
                corners.append(p)
    return corners
