import unittest

from traffic_queue.consensus import combine


class ConsensusTests(unittest.TestCase):
    def test_agreement_retains_votes_and_lowest_evidence_score(self):
        first = dict(recording="r", frame_index=0, lane="lane", time=0,
                     model="a", state="estimate", count=2, confidence=0.85)
        second = dict(first, model="b", confidence=0.65)
        row, = combine([[first], [second]])
        self.assertEqual((row["state"], row["count"], row["confidence"]), ("estimate", 2, 0.65))
        self.assertEqual(len(row["model_votes"]), 2)

    def test_disagreement_abstains_and_misalignment_is_rejected(self):
        first = dict(recording="r", frame_index=0, lane="lane", time=0,
                     model="a", state="estimate", count=2, confidence=0.85)
        row, = combine([[first], [dict(first, model="b", count=3)]])
        self.assertEqual((row["state"], row["count"]), ("uncertain", None))
        with self.assertRaisesRegex(ValueError, "frame order"):
            combine([[first], [dict(first, frame_index=1)]])
