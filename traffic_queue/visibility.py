"""Explicit camera-clock evidence that a review confirmed a lane was empty."""

from bisect import bisect_right
from math import isfinite


class EmptyLaneEvidence:
    def __init__(self, entries, lanes):
        self.entries = {}
        for lane, entry in entries.items():
            if lane not in lanes or not isinstance(entry["source"], str) or not entry["source"].strip():
                raise ValueError("Empty-lane evidence needs a configured lane and a source")
            intervals = entry["intervals"]
            previous_end = 0
            for start, end in intervals:
                if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and isfinite(x)
                           for x in (start, end)) or not previous_end <= start < end:
                    raise ValueError("Empty-lane intervals must be ordered, finite and non-overlapping")
                previous_end = end
            self.entries[lane] = (entry["source"], intervals, [start for start, _ in intervals])

    def at(self, time, blocked):
        result = {}
        for lane, (source, intervals, starts) in self.entries.items():
            index = bisect_right(starts, time) - 1
            if index >= 0 and time < intervals[index][1] and lane not in blocked:
                result[lane] = source
        return result
