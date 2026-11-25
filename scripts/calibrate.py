"""Create a camera configuration from operator-marked image and ground anchors."""

import argparse
import json
from math import hypot
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traffic_queue.geometry import project


def calibrate(layout):
    import cv2
    import numpy as np

    image = np.asarray(layout["image_anchors"], dtype=float)
    ground = np.asarray(layout["ground_anchors"], dtype=float)
    if image.shape != ground.shape or image.shape != (4, 2):
        raise ValueError("Supply four matching image and ground anchors")
    matrix = cv2.getPerspectiveTransform(image.astype("float32"), ground.astype("float32"))
    if abs(np.linalg.det(matrix)) < 1e-12:
        raise ValueError("Degenerate ground-plane calibration")
    lanes = []
    for raw in layout["lanes"]:
        pixels, stop, end = raw["polygon"], raw["stop"], raw["visible_end"]
        mapped_stop, mapped_end = project(stop, matrix), project(end, matrix)
        upstream = [b - a for a, b in zip(mapped_stop, mapped_end)]
        image_upstream = [b - a for a, b in zip(stop, end)]
        lanes.append({
            "id": raw["id"],
            "polygon": [project(point, matrix) for point in pixels],
            "stop": mapped_stop, "upstream": upstream, "visible_distance": hypot(*upstream),
            "image_polygon": pixels, "image_stop": stop, "image_upstream": image_upstream,
            "image_visible_distance": hypot(*image_upstream),
        })
    evidence = {key: layout[key] for key in ("phase_events", "reviewed_empty") if key in layout}
    return {"image_to_ground": matrix.tolist(), "lanes": lanes, "provenance": layout["provenance"], **evidence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path)
    parser.add_argument("camera", type=Path)
    args = parser.parse_args()
    result = calibrate(json.loads(args.layout.read_text()))
    with args.camera.open("x") as output:
        json.dump(result, output, indent=2)


if __name__ == "__main__":
    main()
