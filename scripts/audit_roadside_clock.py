"""Measure frame-clock and labelled reference overlap for a roadside sample."""

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frame_timing", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("--timezone", required=True, help="IANA timezone for the camera CSV")
    args = parser.parse_args()
    zone = ZoneInfo(args.timezone)
    with args.frame_timing.open(newline="") as source:
        frames = [(int(row["Image_number"]), datetime.strptime(row["Timestamp"], "%Y-%m-%d-%H-%M-%S_%f")
                   .replace(tzinfo=zone).timestamp()) for row in csv.DictReader(source)]
    with args.reference.open(newline="") as source:
        reader = csv.DictReader(source)
        references = [float(row["Time"]) for row in reader]
    if not frames or not references or any(a[0] >= b[0] or a[1] >= b[1] for a, b in zip(frames, frames[1:])):
        raise ValueError("Input requires nonempty reference times and ordered camera frames")
    start, end = frames[0][1], frames[-1][1]
    overlap = sum(start <= time <= end for time in references)
    print(json.dumps({"timezone_assumption": args.timezone, "timestamped_frames": len(frames),
                      "camera_span_seconds": round(end-start, 3), "reference_rows": len(references),
                      "reference_rows_in_camera_time_range": overlap}, indent=2))


if __name__ == "__main__":
    main()
