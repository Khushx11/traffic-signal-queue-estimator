"""Compare queue-state variants on synthetic tracks, separately from video benchmarks."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traffic_queue.estimator import Observation, QueueEstimator
from traffic_queue.evaluation import coverage_curve, score


def run(scenario, recovery):
    lane = scenario["lane"]
    estimator = QueueEstimator({lane: scenario["visible_distance"]}, dwell=0, recovery=recovery)
    rows = []
    for frame in scenario["frames"]:
        observations = [Observation(identity, lane, distance, speed)
                        for identity, distance, speed in frame["tracks"]]
        state = estimator.update(frame["time"], observations, [lane] if frame.get("obscured") else [],
                                 observed_empty=[lane] if frame.get("observed_empty") else [])
        rows.append({"time": frame["time"], "lane": lane, "phase": frame["phase"],
                     "reference": frame["reference"], **state[lane]})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    scenario = json.loads(args.fixture.read_text())
    report = {"kind": scenario["kind"], "methods": {}}
    for label, recovery in [("without_recovery", 0.0), ("with_recovery", 1.0)]:
        rows = run(scenario, recovery)
        report["methods"][label] = {
            "score": score(rows),
            "coverage_curve": coverage_curve(rows, [0, 0.5, 0.75, 1]),
            "rows": rows,
        }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
