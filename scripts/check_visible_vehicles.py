"""Check if manually marked vehicle centres fall inside unique detection boxes."""
import argparse
import json
from pathlib import Path
from hashlib import sha256

from ultralytics import YOLO
import cv2

from infer import VEHICLE_CLASSES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recording", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("checkpoints", type=Path, nargs="+")
    parser.add_argument("--crop", type=int, nargs=4, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    args = parser.parse_args()
    reference = json.loads(args.reference.read_text())
    digest = sha256()
    with args.recording.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != reference["video_sha256"]:
        raise ValueError("Recording does not match the reviewed asset")
    capture = cv2.VideoCapture(str(args.recording))
    models = [(point.name, YOLO(str(point))) for point in args.checkpoints]
    rows = []
    try:
        for item in reference["frames"]:
            capture.set(cv2.CAP_PROP_POS_MSEC, item["time"] * 1000)
            success, frame = capture.read()
            if not success:
                raise ValueError(f"Couldn't decode frame at {item['time']} seconds")
            left_offset = top_offset = 0
            if args.crop:
                left_offset, top_offset, right, bottom = args.crop
                if not (0 <= left_offset < right <= frame.shape[1] and 0 <= top_offset < bottom <= frame.shape[0]):
                    raise ValueError("Crop falls outside the frame")
                frame = frame[top_offset:bottom, left_offset:right]
            for name, model in models:
                result = model.predict(frame, conf=0.25, imgsz=640, device="cpu", verbose=False)[0]
                detections = result.obb if model.task == "obb" else result.boxes
                boxes = [box for box, category in zip(detections.xyxy.tolist(), detections.cls.int().tolist())
                         if result.names[category] in VEHICLE_CLASSES]
                marks = set(range(len(item["points"])))
                for left, top, right, bottom in boxes:
                    left, right = left + left_offset, right + left_offset
                    top, bottom = top + top_offset, bottom + top_offset
                    hits = [i for i in sorted(marks) if left <= item["points"][i][0] <= right
                            and top <= item["points"][i][1] <= bottom]
                    if hits:
                        marks.remove(min(hits, key=lambda i: (item["points"][i][0] - (left+right)/2)**2
                                         + (item["points"][i][1] - (top+bottom)/2)**2))
                rows.append({"time": item["time"], "checkpoint": name, "marked": len(item["points"]),
                             "matched": len(item["points"]) - len(marks)})
    finally:
        capture.release()
    print(json.dumps({"reference_type": reference["reference_type"], "crop": args.crop, "results": rows}, indent=2))


if __name__ == "__main__":
    main()
