"""Read publisher frame timestamps without conflating capture and playback time."""

import csv
from datetime import datetime
from zoneinfo import ZoneInfo


def read_frame_clock(stream, timezone):
    zone = ZoneInfo(timezone)
    frames = []
    for row in csv.DictReader(stream):
        index = int(row["Image_number"])
        clock = datetime.strptime(row["Timestamp"], "%Y-%m-%d-%H-%M-%S_%f").replace(tzinfo=zone)
        epoch_us = round(clock.timestamp() * 1_000_000)
        if index != len(frames) or (frames and epoch_us <= frames[-1]):
            raise ValueError("Capture clock must contain consecutive zero-based frames in time order")
        frames.append(epoch_us)
    if not frames:
        raise ValueError("Capture clock cannot be empty")
    return frames
