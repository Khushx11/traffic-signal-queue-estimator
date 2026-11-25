"""Run a causal vehicle detector and ByteTrack on a locally supplied video."""

import argparse
import json
from collections import deque
from bisect import bisect_right
from statistics import median
from pathlib import Path
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from traffic_queue.estimator import Observation, QueueEstimator
from traffic_queue.geometry import Lane, lane_at, project

from traffic_queue.visibility import EmptyLaneEvidence

VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck", "vehicle"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("camera", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--recording", required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--method", choices=("tracking", "geometry", "temporal"), default="temporal")
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--phase-events", type=Path, help="JSON mapping lane IDs to verified phase transitions")
    parser.add_argument("--approach-crop", action="store_true", help="Magnify the configured lanes with surrounding context")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    import cv2
    from ultralytics import YOLO

    camera = json.loads(args.camera.read_text())
    lanes = [Lane(row["id"], tuple(map(tuple, row["polygon"])), tuple(row["stop"]),
                  tuple(row["upstream"]), row["visible_distance"]) for row in camera["lanes"]]
    phase_data = json.loads(args.phase_events.read_text()) if args.phase_events else camera.get("phase_events", {})
    phase_clocks = {}
    for lane_id, entry in phase_data.items():
        events = entry["events"]
        clock = [event["time"] for event in events]
        if not entry["source"] or any(a >= b for a, b in zip(clock, clock[1:])) or any(
            event["phase"] not in {"red", "amber", "green", None} for event in events
        ):
            raise ValueError("Phase events require ordered timestamps, valid states and source provenance")
        phase_clocks[lane_id] = clock
    reviewed_empty = EmptyLaneEvidence(camera.get("reviewed_empty", {}), {lane.id for lane in lanes})
    matrix = camera["image_to_ground"]
    if args.method == "tracking":
        lanes = [Lane(row["id"], tuple(map(tuple, row["image_polygon"])), tuple(row["image_stop"]),
                      tuple(row["image_upstream"]), row["image_visible_distance"]) for row in camera["lanes"]]
    estimator = QueueEstimator(
        {lane.id: lane.visible_distance for lane in lanes},
        recovery=1.0 if args.method == "temporal" else 0.0,
        **(dict(slow_speed=5, max_gap=30, tail_margin=10) if args.method == "tracking" else {}),
    )
    region = [point for lane in camera["lanes"] for point in lane["image_polygon"]]
    model = YOLO(str(args.weights), task="detect")
    capture = cv2.VideoCapture(str(args.video))
    fps = capture.get(cv2.CAP_PROP_FPS)
    if not capture.isOpened() or fps <= 0:
        raise ValueError("Video is unreadable or frame rate is unknown")
    history = {}
    results = []
    frame_index = 0
    start = perf_counter()
    try:
        while args.max_frames is None or frame_index < args.max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            timestamp = frame_index / fps
            x_offset = y_offset = 0
            image = frame
            if args.approach_crop:
                xs, ys = zip(*region)
                x_offset, y_offset = max(0, int(min(xs)) - 64), max(0, int(min(ys)) - 64)
                right = min(frame.shape[1], int(max(xs)) + 64)
                bottom = min(frame.shape[0], int(max(ys)) + 64)
                image = frame[y_offset:bottom, x_offset:right]
                if image.size == 0:
                    raise ValueError("Camera approach falls outside the recording")
            inference = model.track(image, persist=True, tracker="bytetrack.yaml",
                                    verbose=False, device=args.device)[0]
            boxes = inference.boxes
            observations, evidence, obscured = [], [], set()
            current = set()
            if boxes.id is not None:
                detections = zip(boxes.xyxy.cpu().tolist(), boxes.id.int().cpu().tolist(),
                                 boxes.cls.int().cpu().tolist())
                for box, identity, class_id in detections:
                    label = inference.names[class_id]
                    if label not in VEHICLE_CLASSES:
                        continue
                    x1, y1, x2, y2 = box = [
                        box[0] + x_offset, box[1] + y_offset,
                        box[2] + x_offset, box[3] + y_offset,
                    ]
                    pixel = ((x1 + x2) / 2, (y1 + y2) / 2)
                    point = pixel if args.method == "tracking" else project(pixel, matrix)
                    lane = lane_at(lanes, point)
                    if lane is None:
                        continue
                    distance = lane.distance(point)
                    samples = history.setdefault(identity, deque())
                    if samples and (samples[-1][1] != lane.id or timestamp - samples[-1][0] > 0.3):
                        samples.clear()
                    samples.append((timestamp, lane.id, distance))
                    while timestamp - samples[0][0] > 0.8:
                        samples.popleft()
                    elapsed = timestamp - samples[0][0]
                    distance = median(sample[2] for sample in list(samples)[-3:])
                    speed = abs(distance - median(sample[2] for sample in list(samples)[:3])) / elapsed if elapsed >= 0.4 else float("inf")
                    length = 12.0 if label in {"bus", "truck"} else 4.5
                    if args.method == "tracking":
                        length = 18.0
                    if label in {"bus", "truck"}:
                        obscured.add(lane.id)
                    current.add(identity)
                    observations.append(Observation(identity, lane.id, distance, speed, length))
                    evidence.append({"id": identity, "lane": lane.id, "box": box, "class": label,
                                     "distance": distance, "speed": speed if speed != float("inf") else None})
            history = {identity: history[identity] for identity in current}
            blocked = {item.lane for item in observations} | obscured
            empty_sources = reviewed_empty.at(timestamp, blocked)
            states = estimator.update(timestamp, observations, obscured if args.method == "temporal" else (),
                                      observed_empty=empty_sources)
            for lane_id, state in states.items():
                index = bisect_right(phase_clocks.get(lane_id, ()), timestamp) - 1
                phase = phase_data[lane_id]["events"][index]["phase"] if index >= 0 else None
                results.append({"recording": args.recording, "time": timestamp, "lane": lane_id, "model": f"{args.weights.name}/{args.method}" + ("/crop" if args.approach_crop else ""),
                                "phase": phase, "phase_source": phase_data[lane_id]["source"] if phase else None,
                                "empty_source": empty_sources.get(lane_id) if state["count"] == 0 else None,
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
