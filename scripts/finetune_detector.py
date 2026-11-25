"""Fine-tune a local pretrained detector using training and validation only."""
import argparse
from pathlib import Path

from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Run output already exists")
    YOLO(str(args.checkpoint)).train(
        data=str(args.dataset.resolve()), project=str(args.output.resolve().parent),
        name=args.output.name, epochs=args.epochs, device=args.device,
        imgsz=480, batch=8, workers=0, freeze=10, seed=42,
        optimizer="AdamW", lr0=0.001, mosaic=0, scale=0.3,
        hsv_v=0.35, plots=False, amp=False,
    )


if __name__ == "__main__":
    main()
