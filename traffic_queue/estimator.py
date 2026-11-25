"""Causal per-lane estimation from time-stamped, lane-assigned tracks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Observation:
    id: int
    lane: str
    distance: float
    speed: float
    length: float = 4.5


@dataclass(frozen=True)
class TrackState:
    observation: Observation
    last_seen: float
    slow_since: float


class QueueEstimator:
    def __init__(self, visible_distance, slow_speed=1.0, dwell=1.0, max_gap=8,
                 recovery=1.0, tail_margin=4.0):
        self.visible_distance = dict(visible_distance)
        self.slow_speed = slow_speed
        self.dwell = dwell
        self.max_gap = max_gap
        self.recovery = recovery
        self.tail_margin = tail_margin
        self.tracks = {}
        self.previous_queue = set()
        self.previous_time = None

    def update(self, timestamp, observations, obscured=()):
        if self.previous_time is not None and timestamp <= self.previous_time:
            raise ValueError("Timestamps must be strictly increasing")
        observations = tuple(observations)
        visible = {observation.id: observation for observation in observations}
        if len(visible) != len(observations):
            raise ValueError("Duplicate track ID in frame")
        obscured = set(obscured)
        self.previous_time = timestamp
        for identity, observation in visible.items():
            old = self.tracks.get(identity)
            continuous = (
                old is not None and old.observation.lane == observation.lane
                and timestamp - old.last_seen <= max(self.recovery, self.dwell)
                and abs(old.observation.speed) <= self.slow_speed
                and abs(observation.speed) <= self.slow_speed
            )
            self.tracks[identity] = TrackState(
                observation, timestamp, old.slow_since if continuous else timestamp
            )
        for identity in self.tracks.keys() - visible.keys():
            if timestamp - self.tracks[identity].last_seen > self.recovery:
                del self.tracks[identity]

        queued = set()
        result = {}
        for lane, limit in self.visible_distance.items():
            candidates = sorted(
                (state for state in self.tracks.values()
                 if state.observation.lane == lane and 0 <= state.observation.distance <= limit),
                key=lambda state: state.observation.distance,
            )
            rear = 0.0
            seen_ids, recovered_ids = [], []
            for state in candidates:
                item = state.observation
                carried = item.id not in visible
                if carried and (lane not in obscured or item.id not in self.previous_queue):
                    continue
                if abs(item.speed) > self.slow_speed or timestamp - state.slow_since < self.dwell:
                    continue
                if item.distance - rear > self.max_gap:
                    break
                rear = item.distance + item.length
                queued.add(item.id)
                (recovered_ids if carried else seen_ids).append(item.id)
            state = "estimate"
            count = len(seen_ids) + len(recovered_ids)
            if seen_ids and rear >= limit - self.tail_margin:
                state, count = "lower_bound", len(seen_ids)
            elif lane in obscured and not recovered_ids:
                state, count = "uncertain", None
            result[lane] = {
                "state": state, "count": count, "visible_ids": seen_ids,
                "recovered_ids": recovered_ids, "tail_distance": rear if queued else None,
                "confidence": 0.65 if recovered_ids else (1.0 if state == "estimate" else 0.0),
            }
            if not seen_ids and not recovered_ids:
                result[lane]["tail_distance"] = None
        self.previous_queue = queued
        return result
