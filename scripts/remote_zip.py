"""List an HTTP range-enabled ZIP or extract a selected member."""

import argparse
import io
from pathlib import Path
import re
import shutil
from urllib.request import Request, urlopen
from zipfile import ZipFile


class RemoteArchive(io.RawIOBase):
    def __init__(self, url, block_size=4 * 1024 * 1024):
        self.url = url
        self.block_size = block_size
        self.position = 0
        self.block_start = -1
        self.block = b""
        with urlopen(Request(url, headers={"Range": "bytes=0-0"}), timeout=30) as response:
            match = re.fullmatch(r"bytes 0-0/(\d+)", response.headers.get("Content-Range", ""))
            if response.status != 206 or not match:
                raise OSError("Server does not support byte-range ZIP access")
            self.size = int(match[1])

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        start = {io.SEEK_SET: 0, io.SEEK_CUR: self.position, io.SEEK_END: self.size}
        position = start[whence] + offset
        if position < 0:
            raise ValueError("Negative archive position")
        self.position = position
        return position

    def read(self, count=-1):
        remaining = max(0, self.size - self.position)
        count = remaining if count < 0 else min(count, remaining)
        result = bytearray()
        while count:
            if not self.block_start <= self.position < self.block_start + len(self.block):
                start = self.position
                end = min(self.size, start + self.block_size) - 1
                request = Request(self.url, headers={"Range": f"bytes={start}-{end}"})
                with urlopen(request, timeout=60) as response:
                    if response.status != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{self.size}":
                        raise OSError("Unexpected range response")
                    self.block = response.read(end - start + 1)
                if len(self.block) != end - start + 1:
                    raise OSError("Truncated range response")
                self.block_start = start
            offset = self.position - self.block_start
            part = self.block[offset:offset + count]
            result.extend(part)
            self.position += len(part)
            count -= len(part)
        return bytes(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--member")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preview-bytes", type=int)
    args = parser.parse_args()
    if args.member and not args.output:
        parser.error("--member requires --output")
    if args.preview_bytes is not None and args.preview_bytes <= 0:
        parser.error("--preview-bytes must be positive")
    with RemoteArchive(args.url) as source, ZipFile(source) as archive:
        if not args.member:
            for item in archive.infolist():
                print(f"{item.file_size:14d} {item.filename}")
            return
        with archive.open(args.member) as member, args.output.open("xb") as output:
            if args.preview_bytes is None:
                shutil.copyfileobj(member, output, length=1024 * 1024)
            else:
                remaining = args.preview_bytes
                while remaining:
                    chunk = member.read(min(remaining, 1024 * 1024))
                    if not chunk:
                        break
                    output.write(chunk)
                    remaining -= len(chunk)


if __name__ == "__main__":
    main()
