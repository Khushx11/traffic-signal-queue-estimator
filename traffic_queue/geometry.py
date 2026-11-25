"""Project pixel positions and assign them to exclusive approach lanes."""

from dataclasses import dataclass
from math import hypot
from typing import Optional, Tuple

Point = Tuple[float, float]


def project(point, matrix):
    x, y = point
    u, v, scale = (a * x + b * y + c for a, b, c in matrix)
    if abs(scale) < 1e-9:
        raise ValueError("Point is on the projection horizon")
    return u / scale, v / scale


def contains(polygon, point):
    x, y = point
    inside = False
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


@dataclass(frozen=True)
class Lane:
    id: str
    polygon: Tuple[Point, ...]
    stop: Point
    upstream: Point
    visible_distance: float

    def distance(self, point):
        dx, dy = self.upstream
        norm = hypot(dx, dy)
        if norm == 0:
            raise ValueError("Lane direction must be non-zero")
        return ((point[0] - self.stop[0]) * dx + (point[1] - self.stop[1]) * dy) / norm


def lane_at(lanes, point) -> Optional[Lane]:
    matches = [lane for lane in lanes if contains(lane.polygon, point)]
    return matches[0] if len(matches) == 1 else None
