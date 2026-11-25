"""Serve the review workspace and run local inference on uploaded video bytes."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 150 * 1024 * 1024


class Workspace(SimpleHTTPRequestHandler):
    def __init__(self, *args, weights, **kwargs):
        self.weights = weights
        super().__init__(*args, directory=str(ROOT / "web"), **kwargs)

    def do_POST(self):
        if self.path != "/analyze":
            self.send_error(404)
            return
        if self.headers.get("Origin") != f"http://127.0.0.1:{self.server.server_port}":
            self.send_error(403)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            camera = json.loads(unquote(self.headers.get("X-Camera-Config", "")))
            if not 0 < size <= MAX_BYTES or not isinstance(camera, dict):
                raise ValueError
        except ValueError:
            self.send_error(400, "Supply a camera configuration and a video up to 150 MiB")
            return
        with TemporaryDirectory() as directory:
            work = Path(directory)
            video, config, output = (work / name for name in ("recording", "camera.json", "output.json"))
            with video.open("wb") as stream:
                remaining = size
                while remaining:
                    chunk = self.rfile.read(min(remaining, 1024 * 1024))
                    if not chunk:
                        self.send_error(400, "Incomplete upload")
                        return
                    stream.write(chunk)
                    remaining -= len(chunk)
            if "image_anchors" in camera:
                try:
                    from calibrate import calibrate
                    evidence = {key: camera[key] for key in ("phase_events", "reviewed_empty") if key in camera}
                    camera = {**calibrate(camera), **evidence}
                except (KeyError, TypeError, ValueError, ImportError):
                    self.send_error(400, "Invalid camera layout")
                    return
            config.write_text(json.dumps(camera))
            try:
                subprocess.run([sys.executable, str(ROOT / "scripts/infer.py"), str(video), str(config),
                                str(output), "--weights", str(self.weights), "--recording", "local-upload"],
                               check=True, capture_output=True, timeout=600)
                body = output.read_bytes()
            except (OSError, subprocess.SubprocessError):
                self.send_error(422, "Analysis failed. Check the video, camera configuration and model setup.")
                return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not args.weights.is_file():
        parser.error("Checkpoint file does not exist")
    with ThreadingHTTPServer(("127.0.0.1", args.port),
                             partial(Workspace, weights=args.weights.resolve())) as server:
        print(f"http://127.0.0.1:{server.server_port}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
