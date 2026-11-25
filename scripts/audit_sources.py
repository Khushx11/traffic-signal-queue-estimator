"""Download or audit registered FHWA archives without extracting their contents."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def download(url, target):
    partial = target.with_suffix(".part")
    with urlopen(url, timeout=60) as source, partial.open("wb") as output:
        shutil.copyfileobj(source, output)
    with ZipFile(partial) as archive:
        archive.infolist()
    partial.replace(target)


def inspect(path):
    digest = hashlib.sha256()
    with path.open("rb") as archive:
        for chunk in iter(lambda: archive.read(1024 * 1024), b""):
            digest.update(chunk)
    with ZipFile(path) as archive:
        members = [
            {"path": member.filename, "bytes": member.file_size}
            for member in archive.infolist()
            if not member.is_dir()
        ]
    return {"sha256": digest.hexdigest(), "bytes": path.stat().st_size, "members": members}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=ROOT / "data/local")
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "data/sources.json").read_text())
    args.directory.mkdir(parents=True, exist_ok=True)
    report = []
    for source in manifest["archives"]:
        url = f"{manifest['portal']}/files/{source['asset_id']}?download=true"
        path = args.directory / f"{source['id']}.zip"
        if args.download and not path.exists():
            download(url, path)
        report.append({**source, "url": url, **inspect(path)})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
