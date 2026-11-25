"""Conservative comparison of independent estimators on the same lane clock."""


def combine(runs):
    if len(runs) < 2:
        raise ValueError("Consensus requires two or more model runs")
    if not runs[0] or any(len(run) != len(runs[0]) for run in runs[1:]):
        raise ValueError("Model runs differ in frame coverage")
    result = []
    for primary, *others in zip(*runs):
        identifier = (primary["recording"], primary["frame_index"], primary["lane"], primary["time"])
        if any((row["recording"], row["frame_index"], row["lane"], row["time"]) != identifier for row in others):
            raise ValueError("Model runs differ in lane or frame order")
        votes = [{field: row[field] for field in ("model", "state", "count", "confidence")}
                 for row in (primary, *others)]
        states = {(vote["state"], vote["count"]) for vote in votes}
        row = {**primary, "model": "unanimous-consensus", "model_votes": votes,
               "overlay_source": primary["model"], "confidence": min(vote["confidence"] for vote in votes)}
        # Track IDs and position estimates belong to one model, so retain their provenance.
        if len(states) != 1:
            row.update(state="uncertain", count=None, confidence=0.0, visible_ids=[],
                       recovered_ids=[], tail_distance=None, empty_source=None)
        result.append(row)
    return result
