"""Retrieve the registered roadside video and timing files without fetching other sensors."""

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from remote_zip import RemoteArchive

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--run", choices=("1003", "1023", "108", "1290"))
    args = parser.parse_args()
    source = json.loads((ROOT / "data/roadside-sources.json").read_text())["sources"][0]
    args.output.mkdir(parents=True, exist_ok=True)
    paths = [(member, args.output / Path(member).name) for member in source["members"]
             if args.run is None or Path(member).parent.name == f"Run_{args.run}"]
    if any(path.exists() for _, path in paths):
        parser.error("Choose a directory without existing sample files")
    report = {}
    with RemoteArchive(source["archive"], 8 * 1024 * 1024) as remote, ZipFile(remote) as archive:
        for member, path in paths:
            digest = hashlib.sha256()
            temporary = path.with_suffix(path.suffix + ".part")
            with archive.open(member) as incoming, temporary.open("xb") as outgoing:
                for chunk in iter(lambda: incoming.read(1024 * 1024), b""):
                    outgoing.write(chunk)
                    digest.update(chunk)
            report[path.name] = digest.hexdigest()
            expected = source.get("sha256", {}).get(path.name)
            if expected and expected != report[path.name]:
                raise ValueError(f"SHA-256 mismatch for {path.name}")
            temporary.rename(path)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
