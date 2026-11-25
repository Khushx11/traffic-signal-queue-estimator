"""Read movement-specific NGSIM transitions with an explicit frame-clock mapping."""

import csv


def transitions(stream, movement, fps, frame_zero=0):
    if movement not in {"Left", "Thru"}:
        raise ValueError("Use Left or Thru movement")
    if fps <= 0:
        raise ValueError("Phase frame rate must be positive")
    columns = {f"{prefix}_{movement}": state for prefix, state in
               (("BG", "green"), ("BY", "amber"), ("BR", "red"))}
    events = []
    reader = csv.DictReader(stream)
    if not columns.keys() <= set(reader.fieldnames or []):
        raise ValueError("Missing NGSIM phase columns")
    for row in reader:
        for field, phase in columns.items():
            value = row[field].strip()
            if value and value not in {"-1", "NA"}:
                events.append(((int(value) - frame_zero) / fps, phase))
    events.sort()
    if any(a[0] == b[0] and a[1] != b[1] for a, b in zip(events, events[1:])):
        raise ValueError("Conflicting movement phases at the same time")
    return events


class PhaseTimeline:
    """Map verified phase transitions to either playback or capture time."""

    def __init__(self, entry, capture_available):
        from math import isfinite

        self.source = entry["source"]
        self.clock = entry.get("clock", "playback")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("Phase transitions require source provenance")
        if self.clock not in {"playback", "capture"} or (self.clock == "capture" and not capture_available):
            raise ValueError("Capture-based phase transitions require a capture clock")
        self.states = []
        self.times = []
        field = "capture_time_us" if self.clock == "capture" else "time"
        for event in entry["events"]:
            time, state = event[field], event["phase"]
            valid = (type(time) is int if self.clock == "capture" else
                     type(time) in (int, float) and isfinite(time))
            if (not valid or time < 0 or (self.times and time <= self.times[-1])
                    or state not in ("green", "amber", "red", None)):
                raise ValueError("Phase transitions require ordered timestamps and valid states")
            self.times.append(time)
            self.states.append(state)

    def at(self, playback, capture_us):
        from bisect import bisect_right

        time = capture_us if self.clock == "capture" else playback
        index = bisect_right(self.times, time) - 1
        return self.states[index] if index >= 0 else None
