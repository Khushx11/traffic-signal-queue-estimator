"""Extract observed signal-group transitions from the USDOT sample's offline PCAP."""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import struct


def payloads(stream):
    header = stream.read(24)
    if header[:4] != bytes.fromhex("d4c3b2a1") or len(header) != 24 or struct.unpack_from("<I", header, 20)[0] != 1:
        raise ValueError("Expected a classic little-endian microsecond Ethernet PCAP")
    while record := stream.read(16):
        if len(record) != 16:
            raise ValueError("Truncated packet header")
        seconds, micros, size, _ = struct.unpack("<IIII", record)
        if size > 262144 or micros >= 1_000_000:
            raise ValueError("Invalid packet metadata")
        packet = stream.read(size)
        if len(packet) != size:
            raise ValueError("Truncated packet")
        if len(packet) < 42 or packet[12:14] != b"\x08\x00" or packet[23] != 17:
            continue
        udp = 14 + (packet[14] & 15) * 4
        if udp < 34 or len(packet) < udp + 8:
            continue
        length = struct.unpack_from(">H", packet, udp + 4)[0]
        if length < 8 or udp + length > len(packet):
            continue
        lines = dict(line.split(b"=", 1) for line in packet[udp + 8:udp + length].splitlines() if b"=" in line)
        if lines.get(b"Type", b"").upper() == b"SPAT" and b"Payload" in lines:
            yield seconds * 1_000_000 + micros, bytes.fromhex(lines[b"Payload"].decode("ascii"))


def decode(stream):
    import j2735_201603_combined

    message = j2735_201603_combined.DSRC.MessageFrame
    groups = defaultdict(list)
    count = 0
    first = last = None
    for capture_time, payload in payloads(stream):
        if last is not None and capture_time < last:
            raise ValueError("SPaT packet timestamps must be ordered")
        message.from_uper(payload)
        decoded = json.loads(message.to_jer())
        if decoded["messageId"] != 19:
            raise ValueError("SPaT envelope contained a different message type")
        count += 1
        first = capture_time if first is None else first
        last = capture_time
        for intersection in decoded["value"]["intersections"]:
            identity = intersection["id"]
            for movement in intersection["states"]:
                events = movement["state-time-speed"]
                if not events:
                    continue
                # The first entry is the current event. Later events are forecasts.
                state = events[0]["eventState"]
                key = f"{identity.get('region', '-')}/{identity['id']}/{movement['signalGroup']}"
                history = groups[key]
                if not history or history[-1]["event_state"] != state:
                    history.append({"capture_time_us": capture_time, "event_state": state})
    if not count:
        raise ValueError("No SPaT payloads found")
    return {"decoded_messages": count, "first_packet_time_us": first,
            "last_packet_time_us": last, "lane_mapping_verified": False,
            "signal_groups": dict(sorted(groups.items()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    args = parser.parse_args()
    with args.capture.open("rb") as stream:
        print(json.dumps(decode(stream), indent=2))


if __name__ == "__main__":
    main()
