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
