import io
import unittest

from traffic_queue.phases import transitions


class MovementClockTests(unittest.TestCase):
    def test_frame_zero_and_movement_are_explicit(self):
        source = io.StringIO("BG_Left,BY_Left,BR_Left,BG_Thru,BY_Thru,BR_Thru\n20,40,50,30,60,70\n")
        self.assertEqual(transitions(source, "Thru", 10, frame_zero=20),
                         [(1.0, "green"), (4.0, "amber"), (5.0, "red")])
