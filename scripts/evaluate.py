"""Join predictions and audited references on the same physical recording clock."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traffic_queue.evaluation import coverage_curve, cycle_peaks, score, subgroup_scores, validate_split


def key(row, clock):
    if clock == "capture":
        value = row.get("capture_time_us")
        if type(value) is not int or value < 0:
            raise ValueError("Capture matching requires integer capture_time_us on every row")
    else:
        value = round(row["time"] * 1000)
    return row["recording"], row["lane"], value


def join(predictions, reference, *, allow_reviewed_empty=False, clock="playback"):
    indexed = {}
    for prediction in predictions:
        identifier = key(prediction, clock)
        if identifier in indexed:
            raise ValueError(f"Duplicate prediction {identifier}")
        indexed[identifier] = prediction
    rows, seen = [], set()
    for item in reference:
        identifier = key(item, clock)
        if identifier in seen:
            raise ValueError(f"Duplicate reference {identifier}")
        seen.add(identifier)
        prediction = indexed.get(identifier, {"state": "uncertain", "count": None, "confidence": 0})
        if prediction.get("empty_source") and not allow_reviewed_empty:
            raise ValueError(f"Operator-assisted zero at {identifier}; use an unassisted prediction run")
        rows.append({**item, **{field: prediction[field] for field in ("state", "count", "confidence")}})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--split", default="test")
    parser.add_argument("--allow-reviewed-empty", action="store_true",
                        help="Report operator-assisted results separately")
    parser.add_argument("--join-clock", choices=("playback", "capture"), default="playback")
    args = parser.parse_args()
    references = json.loads(args.reference.read_text())
    validate_split(references)
    selected = [row for row in references if row["split"] == args.split]
    if not selected:
        parser.error("No reference rows found for this split")
    rows = join(json.loads(args.predictions.read_text()), selected,
                allow_reviewed_empty=args.allow_reviewed_empty, clock=args.join_clock)
    report = {
        "split": args.split,
        "join_clock": args.join_clock,
        "mode": "operator-assisted" if args.allow_reviewed_empty else "unassisted",
        "empty_lane": score([row for row in rows if row["reference"] == 0]),
        "nonempty_lane": score([row for row in rows if row["reference"] is not None and row["reference"] > 0]),
        "overall": score(rows),
        "cycle_peak": cycle_peaks(rows),
        "intersection": subgroup_scores(rows, "intersection"),
        "occlusion": subgroup_scores(rows, "occlusion"),
        "phase": subgroup_scores(rows, "phase"),
        "error_vs_coverage": coverage_curve(rows, [0, 0.25, 0.5, 0.75, 1]),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
