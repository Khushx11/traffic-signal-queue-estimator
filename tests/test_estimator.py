import unittest

from traffic_queue.estimator import Observation, QueueEstimator


class QueueStateTests(unittest.TestCase):
    def test_duplicate_tracks_are_rejected(self):
        estimator = QueueEstimator({"north": 15})
        item = Observation(1, "north", 3, 0)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            estimator.update(0, [item, item])

    def test_recovery_expires(self):
        estimator = QueueEstimator({"north": 30})
        item = Observation(1, "north", 2, 0)
        estimator.update(0, [item])
        self.assertEqual(estimator.update(1, [item])["north"]["count"], 1)
        hidden = estimator.update(1.5, [], {"north"})["north"]
        self.assertEqual(hidden["recovered_ids"], [1])
        expired = estimator.update(2.5, [], {"north"})["north"]
        self.assertEqual(expired["state"], "uncertain")

    def test_visible_tail_is_a_lower_bound(self):
        estimator = QueueEstimator({"north": 15}, dwell=0)
        items = [Observation(1, "north", 2, 0), Observation(2, "north", 10, 0)]
        lane = estimator.update(0, items)["north"]
        self.assertEqual((lane["state"], lane["count"]), ("lower_bound", 2))

    def test_green_discharge_clears_moving_tracks(self):
        estimator = QueueEstimator({"north": 30}, dwell=0)
        estimator.update(0, [Observation(1, "north", 2, 0)])
        lane = estimator.update(1, [Observation(1, "north", 1, 4)])["north"]
        self.assertEqual(lane["count"], 0)
