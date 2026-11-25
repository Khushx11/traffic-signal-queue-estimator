import io
import struct
import unittest

from scripts.decode_roadside_spat import payloads


class SpatCaptureTests(unittest.TestCase):
    @staticmethod
    def capture(envelope):
        packet = bytearray(42)
        packet[12:14] = b"\x08\x00"
        packet[14] = 0x45
        packet[23] = 17
        struct.pack_into(">H", packet, 38, len(envelope) + 8)
        packet.extend(envelope)
        header = struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 262144, 1)
        return header + struct.pack("<IIII", 123, 456, len(packet), len(packet)) + packet

    def test_extracts_only_spat_and_preserves_microseconds(self):
        stream = io.BytesIO(self.capture(b"Type=SPAT\nPayload=001300\n"))
        self.assertEqual(list(payloads(stream)), [(123000456, bytes.fromhex("001300"))])
        stream = io.BytesIO(self.capture(b"Type=OTHER\nPayload=001300\n"))
        self.assertEqual(list(payloads(stream)), [])

    def test_rejects_truncated_packet(self):
        stream = io.BytesIO(self.capture(b"Type=SPAT\nPayload=001300\n")[:-1])
        with self.assertRaisesRegex(ValueError, "Truncated packet"):
            list(payloads(stream))


class LanePhaseMappingTests(unittest.TestCase):
    def test_preserves_unknown_phase_and_ends_at_capture_boundary(self):
        from scripts.map_roadside_phases import lane_phases

        audit = {"last_packet_time_us": 10, "signal_groups": {
            "group": [{"capture_time_us": 1, "event_state": "protected-Movement-Allowed"},
                      {"capture_time_us": 4, "event_state": "unavailable"}]}}
        result = lane_phases(audit, {"source": "reviewed map", "lanes": {"lane": "group"}})
        self.assertEqual(result["lane"]["clock"], "capture")
        self.assertEqual(result["lane"]["events"], [
            {"capture_time_us": 1, "phase": "green"},
            {"capture_time_us": 4, "phase": None},
            {"capture_time_us": 11, "phase": None},
        ])
