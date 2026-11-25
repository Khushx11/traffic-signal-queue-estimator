"""Measure frame-clock and labelled reference overlap for a roadside sample."""

import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traffic_queue.frame_clock import read_frame_clock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frame_timing", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("--timezone", required=True, help="IANA timezone for the camera CSV")
    args = parser.parse_args()
    with args.frame_timing.open(newline="") as source:
        frames = read_frame_clock(source, args.timezone)
    with args.reference.open(newline="") as source:
        reader = csv.DictReader(source)
        references = [float(row["Time"]) for row in reader]
    if not references:
        raise ValueError("Input requires nonempty reference times")
    start, end = frames[0] / 1_000_000, frames[-1] / 1_000_000
    overlap = sum(start <= time <= end for time in references)
    print(json.dumps({"timezone_assumption": args.timezone, "timestamped_frames": len(frames),
                      "camera_span_seconds": round(end-start, 3), "reference_rows": len(references),
                      "reference_rows_in_camera_time_range": overlap}, indent=2))


if __name__ == "__main__":
    main()
