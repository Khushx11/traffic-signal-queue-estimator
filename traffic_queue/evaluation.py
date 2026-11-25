"""Score queue estimates against eligible, independently assembled references."""

from collections import defaultdict
from statistics import mean


def score(rows, threshold=0.0):
    eligible = [row for row in rows if row["reference"] is not None]
    estimates = [
        row for row in eligible
        if row["state"] == "estimate" and row["confidence"] >= threshold
    ]
    errors = [row["count"] - row["reference"] for row in estimates]
    bounds = [row for row in eligible if row["state"] == "lower_bound"]
    return {
        "eligible": len(eligible),
        "estimated": len(estimates),
        "coverage": len(estimates) / len(eligible) if eligible else None,
        "mae": mean(map(abs, errors)) if errors else None,
        "bias": mean(errors) if errors else None,
        "lower_bounds": len(bounds),
        "invalid_lower_bounds": sum(row["count"] > row["reference"] for row in bounds),
    }


def subgroup_scores(rows, field):
    groups = defaultdict(list)
    for row in rows:
        group = row[field] if row[field] is not None else "(unknown)"
        groups[group].append(row)
    return {group: score(samples) for group, samples in sorted(groups.items())}


def coverage_curve(rows, thresholds):
    return [{"threshold": threshold, **score(rows, threshold)} for threshold in thresholds]


def validate_split(records):
    by_intersection = defaultdict(set)
    for record in records:
        by_intersection[record["intersection"]].add(record["split"])
    leaked = sorted(site for site, splits in by_intersection.items() if len(splits) > 1)
    if leaked:
        raise ValueError("Intersection split overlap: " + ", ".join(leaked))


def cycle_peaks(rows):
    """Report peak error for fully covered, independently verified lane cycles."""
    groups = defaultdict(list)
    for row in rows:
        if row.get("cycle") is not None:
            groups[row["recording"], row["lane"], row["cycle"]].append(row)
    errors = []
    for group in groups.values():
        clocks = {tuple(row.get(field) for field in ("cycle_start_ms", "cycle_end_ms", "cycle_step_ms"))
                  for row in group}
        if len(clocks) != 1:
            continue
        start, end, step = clocks.pop()
        if any(type(value) is not int for value in (start, end, step)):
            continue
        stamps = sorted(round(row["time"] * 1000) for row in group)
        if step <= 0 or end <= start or len(stamps) < 2:
            continue
        expected = range(start, end, step)
        if len(stamps) != len(expected) or any(a != b for a, b in zip(stamps, expected)):
            continue
        if all(row["reference"] is not None and row["state"] == "estimate" for row in group):
            errors.append(max(row["count"] for row in group) - max(row["reference"] for row in group))
    return {"cycles": len(groups), "scored_cycles": len(errors),
            "mae": mean(map(abs, errors)) if errors else None}
