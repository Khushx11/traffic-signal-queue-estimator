import unittest

from traffic_queue.occupancy import estimate, fit


class OccupancyTests(unittest.TestCase):
    def test_counts_use_the_fitted_conversion(self):
        coefficients = fit([(0, 0), (0.5, 3), (1, 6)])
        self.assertEqual(estimate(0.65, coefficients), 4)
        self.assertEqual(estimate(0, coefficients), 0)

    def test_degenerate_calibration_remains_finite(self):
        self.assertEqual(estimate(0.4, fit([(0.5, 2), (0.5, 4)])), 3)
