from datetime import datetime, timezone
import io
import unittest

from scripts.evaluate import join
from traffic_queue.frame_clock import read_frame_clock
from traffic_queue.phases import PhaseTimeline


class CaptureClockTests(unittest.TestCase):
    def test_accepts_irregular_but_ordered_capture(self):
        source = io.StringIO("Image_number,Timestamp\n0,2023-11-20-14-53-02_963892\n"
                             "1,2023-11-20-14-53-03_088892\n")
        times = read_frame_clock(source, "America/New_York")
        self.assertEqual(times[0], round(datetime(2023, 11, 20, 19, 53, 2, 963892, tzinfo=timezone.utc).timestamp() * 1_000_000))
        self.assertEqual(times[1] - times[0], 125000)

    def test_rejects_missing_frame(self):
        source = io.StringIO("Image_number,Timestamp\n1,2023-11-20-14-53-02_963892\n")
        with self.assertRaisesRegex(ValueError, "consecutive"):
            read_frame_clock(source, "UTC")

    def test_capture_join_uses_exact_clock_and_rejects_missing_time(self):
        key = dict(recording="r", lane="a", capture_time_us=1700000000100000)
        prediction = dict(key, time=1, state="estimate", count=3, confidence=0.85)
        reference = dict(key, time=2, reference=3)
        self.assertEqual(join([prediction], [reference], clock="capture")[0]["count"], 3)
        self.assertIsNone(join([prediction], [reference])[0]["count"])
        del reference["capture_time_us"]
        with self.assertRaisesRegex(ValueError, "capture_time_us"):
            join([prediction], [reference], clock="capture")

    def test_capture_phase_ignores_playback_time(self):
        entry = {"source": "controller", "clock": "capture",
                 "events": [{"capture_time_us": 1700000000100000, "phase": "red"}]}
        timeline = PhaseTimeline(entry, True)
        self.assertIsNone(timeline.at(100, 1700000000099999))
        self.assertEqual(timeline.at(1, 1700000000100000), "red")
        with self.assertRaisesRegex(ValueError, "require a capture clock"):
            PhaseTimeline(entry, False)
