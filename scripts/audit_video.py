"""Check decoded coverage and decoder integrity of a video before benchmarking."""

import argparse
import json
from pathlib import Path
import re
import subprocess


def audit(video, ffmpeg):
    completed = subprocess.run(
        [ffmpeg, "-nostdin", "-nostats", "-progress", "pipe:1", "-i", str(video),
         "-map", "0:v:0", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    progress = dict(line.split("=", 1) for line in completed.stdout.splitlines() if "=" in line)
    diagnostics = completed.stderr.splitlines()
    faults = [line for line in diagnostics if re.search(r"corrupt|damaged|invalid data|error while decoding", line, re.I)]
    return {
        "frames": int(progress["frame"]),
        "decoded_duration_seconds": int(progress["out_time_us"]) / 1_000_000,
        "decoder_fault_messages": len(faults),
        "decoder_faults": faults,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--expected-duration", type=float)
    args = parser.parse_args()
    result = audit(args.video, args.ffmpeg)
    result["expected_duration_seconds"] = args.expected_duration
    result["coverage_complete"] = (None if args.expected_duration is None else
                                   result["decoded_duration_seconds"] >= args.expected_duration)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
