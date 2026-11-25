"""Convert decoded movement states to capture-clock lane phases using reviewed mappings."""

import argparse
import json
from pathlib import Path

PHASES = {
    "stop-And-Remain": "red",
    "protected-Movement-Allowed": "green",
    "protected-clearance": "amber",
}


def lane_phases(audit, mappings):
    source = mappings.get("source")
    lanes = mappings.get("lanes")
    if not isinstance(source, str) or not source.strip() or not isinstance(lanes, dict) or not lanes:
        raise ValueError("Provide lane assignments and their independently reviewed source")
    result = {}
    for lane, group in lanes.items():
        if group not in audit["signal_groups"]:
            raise ValueError(f"Signal group unavailable for {lane}: {group}")
        events = [{"capture_time_us": row["capture_time_us"], "phase": PHASES.get(row["event_state"])}
                  for row in audit["signal_groups"][group]]
        if not events:
            raise ValueError(f"Signal group has no observations for {lane}")
        events.append({"capture_time_us": audit["last_packet_time_us"] + 1, "phase": None})
        result[lane] = {"clock": "capture", "source": f"{source} · SPaT group {group}", "events": events}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", type=Path)
    parser.add_argument("mapping", type=Path)
    args = parser.parse_args()
    print(json.dumps(lane_phases(json.loads(args.audit.read_text()),
                                 json.loads(args.mapping.read_text())), indent=2))


if __name__ == "__main__":
    main()
