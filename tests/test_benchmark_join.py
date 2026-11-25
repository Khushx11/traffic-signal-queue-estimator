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
        for time, row in zip((0, 1, 0), rows):
            row.update(time=time, cycle_start_ms=0, cycle_end_ms=2000, cycle_step_ms=1000)
        self.assertEqual(cycle_peaks(rows[:1])["scored_cycles"], 0)
        self.assertEqual(cycle_peaks(rows), {"cycles": 2, "scored_cycles": 1, "mae": 1})

    def test_reviewed_zero_is_rejected_in_unassisted_benchmark(self):
        key = dict(recording="source", lane="A", time=1)
        prediction = dict(key, state="estimate", count=0, confidence=0.85, empty_source="operator")
        reference = dict(key, reference=0)
        with self.assertRaisesRegex(ValueError, "Operator-assisted"):
            join([prediction], [reference])
        self.assertEqual(join([prediction], [reference], allow_reviewed_empty=True)[0]["count"], 0)
