"""Join predictions and audited references on the same physical recording clock."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traffic_queue.evaluation import coverage_curve, cycle_peaks, score, subgroup_scores, validate_split


def key(row):
    return row["recording"], row["lane"], round(row["time"] * 1000)


def join(predictions, reference):
    indexed = {}
    for prediction in predictions:
        identifier = key(prediction)
        if identifier in indexed:
            raise ValueError(f"Duplicate prediction {identifier}")
        indexed[identifier] = prediction
    rows, seen = [], set()
    for item in reference:
        identifier = key(item)
        if identifier in seen:
            raise ValueError(f"Duplicate reference {identifier}")
        seen.add(identifier)
        prediction = indexed.get(identifier, {"state": "uncertain", "count": None, "confidence": 0})
        rows.append({**item, **{field: prediction[field] for field in ("state", "count", "confidence")}})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--split", default="test")
    args = parser.parse_args()
    references = json.loads(args.reference.read_text())
    validate_split(references)
    selected = [row for row in references if row["split"] == args.split]
    if not selected:
        parser.error("No reference rows found for this split")
    rows = join(json.loads(args.predictions.read_text()), selected)
    report = {
        "split": args.split,
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
