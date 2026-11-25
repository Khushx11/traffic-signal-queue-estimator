"""Development-fitted lane occupancy baseline."""

from math import floor
from statistics import mean


def fit(samples):
    """Fit a non-negative affine count conversion from occupancy fractions."""
    pairs = list(samples)
    if not pairs:
        raise ValueError("Calibration requires development samples")
    x_mean = mean(x for x, _ in pairs)
    y_mean = mean(y for _, y in pairs)
    variance = sum((x - x_mean) ** 2 for x, _ in pairs)
    slope = sum((x - x_mean) * (y - y_mean) for x, y in pairs) / variance if variance else 0
    slope = max(0, slope)
    return y_mean - slope * x_mean, slope


def estimate(fraction, calibration):
    if not 0 <= fraction <= 1:
        raise ValueError("Occupancy must be a fraction")
    offset, slope = calibration
    return max(0, floor(offset + slope * fraction + 0.5))
