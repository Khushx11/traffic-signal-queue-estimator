"""Extract causal background-subtraction occupancy from configured lanes."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("camera", type=Path)
    parser.add_argument("--recording", required=True)
    parser.add_argument("--max-frames", type=int)
    args = parser.parse_args()
    import cv2
    import numpy as np

    lanes = json.loads(args.camera.read_text())["lanes"]
    capture = cv2.VideoCapture(str(args.video))
    fps = capture.get(cv2.CAP_PROP_FPS)
    if not capture.isOpened() or fps <= 0:
        raise ValueError("Video is unreadable or frame rate is unknown")
    subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
    masks = {}
    index = 0
    try:
        while args.max_frames is None or index < args.max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            if not masks:
                for lane in lanes:
                    region = np.zeros(frame.shape[:2], dtype=np.uint8)
                    cv2.fillPoly(region, [np.rint(lane["image_polygon"]).astype(np.int32)], 1)
                    masks[lane["id"]] = region.astype(bool)
            foreground = subtractor.apply(frame) == 255
            for lane_id, region in masks.items():
                if not region.any():
                    raise ValueError(f"Lane {lane_id} does not intersect the frame")
                print(json.dumps({
                    "time": index / fps, "recording": args.recording, "lane": lane_id,
                    "occupancy": float(foreground[region].mean()),
                }))
            index += 1
    finally:
        capture.release()


if __name__ == "__main__":
    main()
