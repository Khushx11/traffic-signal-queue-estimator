"""Apply a development-only occupancy calibration to a recording."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traffic_queue.occupancy import estimate, fit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_pairs", type=Path)
    parser.add_argument("occupancy_jsonl", type=Path)
    args = parser.parse_args()
    pairs = json.loads(args.development_pairs.read_text())
    if any(row["split"] != "development" for row in pairs):
        raise ValueError("Occupancy calibration accepts development rows only")
    calibration = fit((row["occupancy"], row["reference"]) for row in pairs)
    with args.occupancy_jsonl.open() as stream:
        rows = [
            {**row, "count": estimate(row["occupancy"], calibration),
             "state": "estimate", "confidence": 1.0, "model": "foreground-occupancy"}
            for row in (json.loads(line) for line in stream)
        ]
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
