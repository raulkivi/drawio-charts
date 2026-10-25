import unittest

from helpers import SCRIPTS_DIR  # noqa: F401

from edge_router import Rect, default_route, route_around, route_crosses


def crosses(points, rect):
    return route_crosses(points, [rect])


class EdgeRouterTest(unittest.TestCase):
    def test_default_route_is_orthogonal_between_facing_sides(self):
        points = default_route(Rect(0, 0, 100, 40), Rect(200, 200, 100, 40))
        self.assertEqual(points[0], (50, 40))     # leaves the bottom
        self.assertEqual(points[-1], (250, 200))  # enters the top
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            self.assertTrue(x1 == x2 or y1 == y2)

    def test_route_crosses(self):
        self.assertTrue(crosses([(0, 50), (300, 50)], Rect(100, 0, 100, 100)))
        self.assertFalse(crosses([(0, 150), (300, 150)], Rect(100, 0, 100, 100)))
        self.assertFalse(crosses([(0, 0), (100, 0)], Rect(100, 0, 100, 100)))  # touching an edge is fine

    def test_route_around_avoids_the_obstacle_with_few_bends(self):
        source, target = Rect(0, 100, 80, 40), Rect(400, 100, 80, 40)
        obstacle = Rect(180, 80, 120, 80)
        self.assertTrue(crosses(default_route(source, target), obstacle))
        waypoints = route_around(source, target, [obstacle])
        self.assertTrue(waypoints)
        full = default_route(source, target, waypoints)
        self.assertFalse(crosses(full, obstacle))
        for (x1, y1), (x2, y2) in zip(full, full[1:]):
            self.assertTrue(abs(x1 - x2) < 0.01 or abs(y1 - y2) < 0.01)
        self.assertLessEqual(len(waypoints), 4)

    def test_no_route_returns_empty(self):
        source, target = Rect(0, 0, 40, 40), Rect(200, 0, 40, 40)
        ring = [Rect(-60, -60, 160, 20), Rect(-60, 80, 160, 20),   # closed box around the source
                Rect(-60, -60, 20, 160), Rect(80, -60, 20, 160)]
        self.assertEqual(route_around(source, target, ring), [])


if __name__ == "__main__":
    unittest.main()
