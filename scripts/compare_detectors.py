"""Compare vehicle detection across unseen datasets and simulated image degradation."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

import cv2
from ultralytics import YOLO

VEHICLES = {"vehicle", "car", "motorcycle", "bus", "truck"}


def iou(a, b):
    intersection = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - intersection
    return intersection / union if union else 0.0


def matches(predictions, targets):
    remaining = set(range(len(targets)))
    matched = set()
    for box in predictions:
        score, index = max(((iou(box, targets[i]), i) for i in remaining), default=(0, -1))
        if score >= 0.5:
            remaining.remove(index)
            matched.add(index)
    return matched


def variants(image):
    height, width = image.shape[:2]
    small = cv2.resize(image, (max(1, width // 3), max(1, height // 3)), interpolation=cv2.INTER_AREA)
    yield "original", image
    yield "blur", cv2.GaussianBlur(image, (15, 15), 4)
    yield "dark", cv2.convertScaleAbs(image, alpha=0.35)
    yield "low_resolution", cv2.resize(small, (width, height), interpolation=cv2.INTER_LINEAR)
    occluded = image.copy()
    occluded[height * 3 // 5:height * 3 // 4, width // 5:width * 4 // 5] = 64
    yield "occlusion_strip", occluded


def evaluate(model, root, split):
    totals = defaultdict(lambda: dict(images=0, objects=0, predicted=0, matched=0,
                                      small_objects=0, small_matched=0, abs_count_error=0))
    for path in sorted((root / "images" / split).glob("*.jpg")):
        image = cv2.imread(str(path))
        height, width = image.shape[:2]
        targets = []
        for label in (root / "labels" / split / (path.stem + ".txt")).read_text().splitlines():
            if label.strip():
                _, x, y, w, h = map(float, label.split())
                targets.append(((x-w/2)*width, (y-h/2)*height, (x+w/2)*width, (y+h/2)*height))
        small = {i for i, box in enumerate(targets) if (box[2]-box[0]) * (box[3]-box[1]) *
                 (480 / max(width, height)) ** 2 < 32 ** 2}
        for condition, frame in variants(image):
            result = model.predict(frame, imgsz=480, conf=0.25, device="cpu", verbose=False)[0]
            predictions = sorted(zip(result.boxes.conf.tolist(), result.boxes.cls.int().tolist(),
                                     result.boxes.xyxy.tolist()), reverse=True)
            boxes = [box for _, label, box in predictions if result.names[label] in VEHICLES]
            tp = matches(boxes, targets)
            t = totals[condition]
            for field, value in (("images", 1), ("objects", len(targets)), ("predicted", len(boxes)),
                                 ("matched", len(tp)), ("small_objects", len(small)),
                                 ("small_matched", len(tp & small)), ("abs_count_error", abs(len(boxes)-len(targets)))):
                t[field] += value
    for t in totals.values():
        t.update(precision=t["matched"]/max(1,t["predicted"]), recall=t["matched"]/max(1,t["objects"]),
                 small_recall=t["small_matched"]/max(1,t["small_objects"]),
                 count_mae=t["abs_count_error"]/t["images"])
    return dict(totals)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("checkpoints", nargs="+", type=Path)
    args = parser.parse_args()
    results = {}
    for checkpoint in args.checkpoints:
        model = YOLO(str(checkpoint))
        results[checkpoint.stem] = {split: evaluate(model, args.dataset, split)
                                    for split in ("test", "external")
                                    if (args.dataset / "images" / split).exists()}
        print("Finished", checkpoint.name, flush=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
