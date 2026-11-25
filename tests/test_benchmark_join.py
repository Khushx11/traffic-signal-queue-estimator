import unittest

from scripts.evaluate import join
from traffic_queue.evaluation import cycle_peaks


class BenchmarkJoinTests(unittest.TestCase):
    def test_other_recordings_cannot_fill_missing_predictions(self):
        reference = {"recording": "first", "lane": "A", "time": 2, "reference": 3}
        prediction = {"recording": "second", "lane": "A", "time": 2, "count": 3,
                      "state": "estimate", "confidence": 1}
        self.assertEqual(join([prediction], [reference])[0]["state"], "uncertain")

    def test_incomplete_cycles_are_outside_peak_error(self):
        rows = [
            dict(recording="video", lane="a", cycle=1, reference=2, state="estimate", count=1),
            dict(recording="video", lane="a", cycle=1, reference=3, state="estimate", count=2),
            dict(recording="video", lane="b", cycle=1, reference=5, state="uncertain", count=None),
        ]
        self.assertEqual(cycle_peaks(rows), {"cycles": 2, "scored_cycles": 1, "mae": 1})
