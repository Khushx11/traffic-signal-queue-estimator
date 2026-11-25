import unittest

from traffic_queue.evaluation import score, validate_split
from traffic_queue.geometry import Lane, lane_at, project


class GeometryTests(unittest.TestCase):
    def test_adjacent_lanes(self):
        left = Lane("left", ((0, 0), (2, 0), (2, 10), (0, 10)), (1, 0), (0, 1), 10)
        right = Lane("right", ((2, 0), (4, 0), (4, 10), (2, 10)), (3, 0), (0, 1), 10)
        self.assertEqual(lane_at([left, right], (1.9, 3)).id, "left")
        self.assertEqual(lane_at([left, right], (2.1, 3)).id, "right")
        self.assertEqual(right.distance((3, 5)), 5)

    def test_project(self):
        matrix = ((2, 0, 4), (0, 2, 6), (0, 0, 2))
        self.assertEqual(project((1, 2), matrix), (3, 5))


class EvaluationTests(unittest.TestCase):
    def test_uncertainty_and_bounds_remain_in_denominator(self):
        rows = [
            dict(reference=4, state="estimate", count=3, confidence=0.9),
            dict(reference=5, state="lower_bound", count=6, confidence=0.8),
            dict(reference=7, state="uncertain", count=None, confidence=0),
            dict(reference=None, state="estimate", count=10, confidence=1),
        ]
        result = score(rows)
        self.assertEqual(result["coverage"], 1 / 3)
        self.assertEqual(result["mae"], 1)
        self.assertEqual(result["bias"], -1)
        self.assertEqual(result["invalid_lower_bounds"], 1)

    def test_rejects_shared_intersection(self):
        records = [
            dict(intersection="A", camera="1", split="development"),
            dict(intersection="A", camera="2", split="test"),
        ]
        with self.assertRaises(ValueError):
            validate_split(records)
