"""Extract one explicitly named archive member to an operator-selected path."""

import argparse
from pathlib import Path
import shutil
from zipfile import ZipFile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("member")
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    with ZipFile(args.archive) as archive, archive.open(args.member) as source:
        with args.destination.open("xb") as destination:
            shutil.copyfileobj(source, destination)


if __name__ == "__main__":
    main()
