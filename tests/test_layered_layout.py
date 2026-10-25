import unittest

from helpers import SCRIPTS_DIR  # noqa: F401

from layered_layout import count_crossings, layered_layout

SIZE = (100, 40)


def boxes(*ids, size=SIZE):
    return [(node_id, *size) for node_id in ids]


def centre(result, node_id, size=SIZE):
    x, y = result.positions[node_id]
    return x + size[0] / 2, y + size[1] / 2


def overlaps(result, sizes):
    ids = list(result.positions)
    found = []
    for i, a in enumerate(ids):
        ax, ay = result.positions[a]
        aw, ah = sizes[a]
        for b in ids[i + 1:]:
            bx, by = result.positions[b]
            bw, bh = sizes[b]
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                found.append((a, b))
    return found


class LayeredLayoutTest(unittest.TestCase):
    def test_chain_top_down_is_one_aligned_column(self):
        result = layered_layout(boxes("A", "B", "C"), [(0, "A", "B"), (1, "B", "C")], "TD")
        (ax, ay), (bx, by), (cx, cy) = (centre(result, n) for n in "ABC")
        self.assertLess(ay, by)
        self.assertLess(by, cy)
        self.assertAlmostEqual(ax, bx)
        self.assertAlmostEqual(bx, cx)

    def test_directions(self):
        edges = [(0, "A", "B")]
        for direction, axis, sign in (("LR", 0, 1), ("RL", 0, -1), ("BT", 1, -1), ("TD", 1, 1)):
            with self.subTest(direction=direction):
                result = layered_layout(boxes("A", "B"), edges, direction)
                delta = centre(result, "B")[axis] - centre(result, "A")[axis]
                self.assertGreater(delta * sign, 0)

    def test_cycle_is_broken_not_fatal(self):
        result = layered_layout(boxes("A", "B", "C"), [(0, "A", "B"), (1, "B", "C"), (2, "C", "A")], "TD")
        ys = [centre(result, n)[1] for n in "ABC"]
        self.assertEqual(ys, sorted(ys))
        self.assertEqual(len(set(ys)), 3)

    def test_long_edges_get_waypoints_short_ones_do_not(self):
        edges = [(0, "A", "B"), (1, "B", "C"), (2, "C", "D"), (3, "A", "D")]
        result = layered_layout(boxes("A", "B", "C", "D"), edges, "TD")
        self.assertEqual(result.edge_points[0], [])
        self.assertEqual(len(result.edge_points[3]), 2)

    def test_crossings_are_removed(self):
        # Input order puts c before d, but a->d and b->c: the layout must swap them.
        result = layered_layout(boxes("a", "b", "c", "d"), [(0, "a", "d"), (1, "b", "c")], "TD")
        ax, bx, cx, dx = (centre(result, n)[0] for n in "abcd")
        self.assertEqual(ax < bx, dx < cx)

    def test_count_crossings(self):
        layers = [["a", "b"], ["c", "d"]]
        self.assertEqual(count_crossings(layers, [("a", "d"), ("b", "c")]), 1)
        self.assertEqual(count_crossings(layers, [("a", "c"), ("b", "d")]), 0)

    def test_no_overlaps_with_mixed_sizes_and_components(self):
        nodes = [("A", 160, 60), ("B", 80, 40), ("C", 120, 90), ("D", 100, 40), ("E", 60, 60), ("F", 200, 40), ("G", 90, 30)]
        edges = [(0, "A", "B"), (1, "A", "C"), (2, "A", "D"), (3, "B", "E"), (4, "C", "E"), (5, "D", "E"), (6, "F", "G")]
        sizes = {n: (w, h) for n, w, h in nodes}
        for direction in ("TD", "LR"):
            with self.subTest(direction=direction):
                result = layered_layout(nodes, edges, direction)
                self.assertEqual(overlaps(result, sizes), [])
                width, height = result.size
                for node_id, (x, y) in result.positions.items():
                    self.assertGreaterEqual(x, 0)
                    self.assertGreaterEqual(y, 0)
                    self.assertLessEqual(x + sizes[node_id][0], width)
                    self.assertLessEqual(y + sizes[node_id][1], height)

    def test_single_node_and_self_loop(self):
        result = layered_layout(boxes("A"), [(0, "A", "A")], "TD")
        self.assertEqual(result.positions["A"], (0, 0))
        self.assertEqual(result.size, SIZE)
        self.assertEqual(result.edge_points[0], [])

    def test_deterministic(self):
        nodes = boxes(*"ABCDEF")
        edges = [(i, a, b) for i, (a, b) in enumerate(["AB", "AC", "BD", "CD", "DE", "AF", "FE"])]
        self.assertEqual(layered_layout(nodes, edges, "TD"), layered_layout(nodes, edges, "TD"))


if __name__ == "__main__":
    unittest.main()
