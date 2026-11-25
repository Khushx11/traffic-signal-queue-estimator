"""Build bounded, reproducible vehicle detection splits from publisher archives."""
import argparse
from collections import defaultdict
from hashlib import sha256
import csv
import io
import json
import re
from pathlib import Path
import tarfile
from zipfile import ZipFile

from PIL import Image

# Source annotations contain spelling and spacing variants for the same class.
TRAFFIC = {"lmv", "lcv", "hmv", "auto", "2w", "car", "bus", "truck", "motorcycle",
           "motorbike", "motor bike", "moterbike", "e-rickshaw", "tractor"}
MIO = {"articulated_truck", "bus", "car", "motorcycle", "motorized_vehicle",
       "pickup_truck", "single_unit_truck", "work_van"}


def read_split(archive, name):
    path = "splits/benchmark/" + ("train/supervised/train.txt" if name == "train" else name + ".txt")
    return sorted(set(archive.read(path).decode().splitlines()))


def write_example(root, split, key, image, boxes):
    with Image.open(io.BytesIO(image)) as decoded:
        width, height = decoded.size
        decoded.verify()
    output = []
    for x1, y1, x2, y2 in boxes:
        x1, x2 = sorted((max(0, min(x1, width)), max(0, min(x2, width))))
        y1, y2 = sorted((max(0, min(y1, height)), max(0, min(y2, height))))
        if x2 > x1 and y2 > y1:
            output.append(f"0 {(x1+x2)/(2*width):.7f} {(y1+y2)/(2*height):.7f} {(x2-x1)/width:.7f} {(y2-y1)/height:.7f}")
    (root / "images" / split / (key + ".jpg")).write_bytes(image)
    (root / "labels" / split / (key + ".txt")).write_text("\n".join(output) + "\n")


def trafficcam(root, images, splits, per_video, train_per_video):
    with ZipFile(images) as archive, ZipFile(splits) as protocol:
        available = set(archive.namelist())
        groups = {}
        for split in ("train", "val", "test"):
            videos = defaultdict(list)
            for item in read_split(protocol, split):
                path = item.removeprefix("raw/")
                if path.startswith("Fully_annotate/") and path + ".json" in available and path + ".jpg" in available:
                    videos[Path(path).parent.name].append(path)
            groups[split] = videos
        if any(set(groups[a]) & set(groups[b]) for a, b in (("train", "val"), ("train", "test"), ("val", "test"))):
            raise ValueError("Official split contains a video shared across selected splits")
        for split, videos in groups.items():
            for video, paths in sorted(videos.items()):
                paths.sort(key=lambda item: (int(re.match(r"frame(\d+)", Path(item).name)[1]), item))
                limit = train_per_video if split == "train" else per_video
                stride = max(1, len(paths) // limit)
                for path in paths[::stride][:limit]:
                    annotation = json.loads(archive.read(path + ".json"))
                    boxes = []
                    for shape in annotation["shapes"]:
                        if shape["label"].strip().lower() in TRAFFIC and len(shape["points"]) >= 2:
                            x, y = zip(*shape["points"])
                            boxes.append((min(x), min(y), max(x), max(y)))
                    write_example(root, split, video + "_" + Path(path).name, archive.read(path + ".jpg"), boxes)


def mio(root, images, toolkit, limit):
    with tarfile.open(toolkit) as archive:
        content = archive.extractfile("MIO-TCD-Localization-Code/gt_train.csv")
        labels = defaultdict(list)
        for name, category, *bounds in csv.reader(io.TextIOWrapper(content)):
            if category in MIO:
                labels[name].append(tuple(map(int, bounds)))
    with tarfile.open(images, mode="r|") as archive:
        count = 0
        for member in archive:
            name = Path(member.name)
            if name.parent.name == "train" and name.suffix == ".jpg" and name.stem in labels:
                write_example(root, "external", name.stem, archive.extractfile(member).read(), labels[name.stem])
                count += 1
                if count == limit:
                    break
    if count != limit:
        raise ValueError(f"Expected {limit} labelled MIO images, found {count}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--trafficcam", nargs=2, type=Path, required=True)
    parser.add_argument("--mio", nargs=2, type=Path)
    parser.add_argument("--per-video", type=int, default=4)
    parser.add_argument("--train-per-video", type=int, default=12)
    args = parser.parse_args()
    if min(args.per_video, args.train_per_video) < 1 or args.output.exists():
        parser.error("Supply a positive sample count and a new output folder")
    root = args.output.resolve()
    splits = ["train", "val", "test"] + (["external"] if args.mio else [])
    for split in splits:
        for folder in ("images", "labels"):
            (root / folder / split).mkdir(parents=True)
    trafficcam(root, *args.trafficcam, args.per_video, args.train_per_video)
    if args.mio:
        mio(root, *args.mio, 80)
    (root / "dataset.yaml").write_text(f"path: {json.dumps(str(root))}\ntrain: images/train\nval: images/val\ntest: images/test\nnames: {{0: vehicle}}\n")
    manifest = {split: sorted(p.stem for p in (root / "images" / split).glob("*.jpg")) for split in splits}
    if any(not images for images in manifest.values()):
        raise ValueError("A requested split is empty")
    previous_splits = set()
    for split, images in manifest.items():
        fingerprints = {sha256((root / "images" / split / (key + ".jpg")).read_bytes()).digest()
                        for key in images}
        if fingerprints & previous_splits:
            raise ValueError(f"Exact duplicate images cross split boundaries at {split}")
        previous_splits.update(fingerprints)
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print({split: len(images) for split, images in manifest.items()})


if __name__ == "__main__":
    main()
