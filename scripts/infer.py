"""Run a causal vehicle detector and ByteTrack on a locally supplied video."""

import argparse
import json
from math import hypot
from pathlib import Path
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traffic_queue.estimator import Observation, QueueEstimator
from traffic_queue.geometry import Lane, lane_at, project

VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("camera", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--method", choices=("tracking", "geometry", "temporal"), default="temporal")
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    import cv2
    from ultralytics import YOLO

    camera = json.loads(args.camera.read_text())
    lanes = [Lane(row["id"], tuple(map(tuple, row["polygon"])), tuple(row["stop"]),
                  tuple(row["upstream"]), row["visible_distance"]) for row in camera["lanes"]]
    matrix = camera["image_to_ground"]
    if args.method == "tracking":
        lanes = [Lane(row["id"], tuple(map(tuple, row["image_polygon"])), tuple(row["image_stop"]),
                      tuple(row["image_upstream"]), row["image_visible_distance"]) for row in camera["lanes"]]
    estimator = QueueEstimator(
        {lane.id: lane.visible_distance for lane in lanes},
        recovery=1.0 if args.method == "temporal" else 0.0,
        **(dict(slow_speed=5, max_gap=30, tail_margin=10) if args.method == "tracking" else {}),
    )
    model = YOLO(str(args.weights), task="detect")
    capture = cv2.VideoCapture(str(args.video))
    fps = capture.get(cv2.CAP_PROP_FPS)
    if not capture.isOpened() or fps <= 0:
        raise ValueError("Video is unreadable or frame rate is unknown")
    previous = {}
    results = []
    frame_index = 0
    start = perf_counter()
    try:
        while args.max_frames is None or frame_index < args.max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            timestamp = frame_index / fps
            inference = model.track(frame, persist=True, tracker="bytetrack.yaml",
                                    verbose=False, device=args.device)[0]
            boxes = inference.boxes
            observations, evidence, obscured = [], [], set()
            current = {}
            if boxes.id is not None:
                detections = zip(boxes.xyxy.cpu().tolist(), boxes.id.int().cpu().tolist(),
                                 boxes.cls.int().cpu().tolist())
                for box, identity, class_id in detections:
                    label = inference.names[class_id]
                    if label not in VEHICLE_CLASSES:
                        continue
                    x1, y1, x2, y2 = box
                    pixel = ((x1 + x2) / 2, y2)
                    point = pixel if args.method == "tracking" else project(pixel, matrix)
                    lane = lane_at(lanes, point)
                    if lane is None:
                        continue
                    old = previous.get(identity)
                    speed = hypot(point[0] - old[0], point[1] - old[1]) * fps if old else float("inf")
                    length = 12.0 if label in {"bus", "truck"} else 4.5
                    if args.method == "tracking":
                        length = 18.0
                    if label in {"bus", "truck"}:
                        obscured.add(lane.id)
                    current[identity] = point
                    observations.append(Observation(identity, lane.id, lane.distance(point), speed, length))
                    evidence.append({"id": identity, "lane": lane.id, "box": box, "class": label})
            previous = current
            states = estimator.update(timestamp, observations, obscured if args.method == "temporal" else ())
            for lane_id, state in states.items():
                results.append({"time": timestamp, "lane": lane_id, "model": f"{args.weights.name}/{args.method}",
                                "phase": None, "phase_source": None,
                                "tracks": [track for track in evidence if track["lane"] == lane_id], **state})
            frame_index += 1
    finally:
        capture.release()
    if not frame_index:
        raise ValueError("No frames were decoded")
    with args.output.open("x") as output:
        json.dump(results, output, indent=2, allow_nan=False)
    print(f"{frame_index} frames in {perf_counter() - start:.2f}s on {args.device}")


if __name__ == "__main__":
    main()
