import unittest

from traffic_queue.estimator import QueueEstimator
from traffic_queue.visibility import EmptyLaneEvidence


class EmptyLaneEvidenceTests(unittest.TestCase):
    def test_reviewed_empty_can_emit_zero_and_blocked_evidence_cannot(self):
        review = EmptyLaneEvidence({"A": {"source": "operator review", "intervals": [[1, 2]]}}, {"A"})
        estimator = QueueEstimator({"A": 20})
        self.assertIsNone(estimator.update(0, [])["A"]["count"])
        self.assertEqual(estimator.update(1, [], observed_empty=review.at(1, set()))["A"]["count"], 0)
        self.assertIsNone(estimator.update(1.5, [], observed_empty=review.at(1.5, {"A"}))["A"]["count"])
        self.assertEqual(review.at(2, set()), {})

    def test_rejects_overlapping_intervals(self):
        with self.assertRaises(ValueError):
            EmptyLaneEvidence({"A": {"source": "review", "intervals": [[0, 3], [2, 4]]}}, {"A"})
