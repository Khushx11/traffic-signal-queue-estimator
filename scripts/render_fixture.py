"""Render an original synthetic sample video from the labelled track fixture."""

import argparse
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw


def render(frame):
    image = Image.new("RGB", (640, 360), "#263e3b")
    draw = ImageDraw.Draw(image)
    draw.rectangle((32, 136, 639, 275), fill="#2e3642")
    draw.rectangle((46, 0, 185, 359), fill="#2e3642")
    draw.line((187, 205, 638, 205), fill="#a88e53", width=2)
    draw.line((208, 208, 208, 274), fill="#e0eae9", width=3)
    draw.rectangle((216, 112, 270, 132), fill="#181e28")
    for index, phase in enumerate(("red", "amber", "green")):
        x = 220 + index * 16
        color = {"red": "#fb7976", "amber": "#ffdd7f", "green": "#6bdfad"}[phase]
        draw.ellipse((x, 116, x + 12, 128), fill=color if phase == frame["phase"] else "#535d64")
    for identity, distance, _ in frame["tracks"]:
        x = 212 + distance * 18
        draw.rounded_rectangle((x, 227, x + 72, 254), 5, fill="#73a3ba" if identity == 1 else "#d0b579")
        draw.rectangle((x + 10, 231, x + 25, 250), fill="#263441")
    if frame.get("obscured"):
        draw.rectangle((219, 217, 288, 260), fill="#50605e")
        draw.text((224, 233), "Occluder", fill="white")
    draw.text((34, 29), "SYNTHETIC SIGNAL CYCLE", fill="#e0eae9")
    draw.text((34, 49), "Illustrative fixture for queue-state review", fill="#a9bec8")
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()
    frames = json.loads(args.fixture.read_text())["frames"]
    command = [args.ffmpeg, "-loglevel", "error", "-f", "rawvideo", "-pixel_format", "rgb24",
               "-video_size", "640x360", "-framerate", "10", "-i", "pipe:0", "-c:v", "libx264",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(args.output)]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        for index, frame in enumerate(frames):
            end = frames[index + 1]["time"] if index + 1 < len(frames) else frame["time"] + 1
            raw = render(frame).tobytes()
            for _ in range(round((end - frame["time"]) * 10)):
                encoder.stdin.write(raw)
        encoder.stdin.close()
        if encoder.wait():
            raise OSError("FFmpeg failed to encode the synthetic video")


if __name__ == "__main__":
    main()
