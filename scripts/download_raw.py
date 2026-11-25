"""Retrieve and verify the complete registered Peachtree pilot camera member."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile

from remote_zip import RemoteArchive

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    collection = json.loads((ROOT / "data/raw-collections.json").read_text())["peachtree"]
    ledger = json.loads((ROOT / "data/verified-assets.json").read_text())
    expected = next(asset["sha256"] for asset in ledger["complete_assets"]
                    if asset["id"] == "peachtree-camera1-0400pm-0415pm-raw")
    output = args.output
    if output.exists():
        parser.error("Output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".part")
    digest = sha256()
    with RemoteArchive(collection["url"], 16 * 1024 * 1024) as remote, ZipFile(remote) as archive:
        with archive.open(collection["pilot_member"]) as source, partial.open("xb") as stream:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                stream.write(chunk)
                digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError(f"SHA-256 mismatch; unverified data retained at {partial}")
    partial.rename(output)
    print(f"{digest.hexdigest()}  {output}")


if __name__ == "__main__":
    main()
