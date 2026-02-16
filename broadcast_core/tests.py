from django.test import SimpleTestCase
from .utils import Timecode

class TimecodeTests(SimpleTestCase):
    def test_init_frames(self):
        tc = Timecode(100)
        self.assertEqual(tc.frames, 100)

    def test_init_string(self):
        # 1 hour = 3600 * 30 = 108000 frames
        tc = Timecode("01:00:00:00")
        self.assertEqual(tc.frames, 108000)

    def test_str_format(self):
        # 30 frames = 1 sec
        tc = Timecode(30)
        self.assertEqual(str(tc), "00:00:01:00")

    def test_addition(self):
        t1 = Timecode(10)
        t2 = Timecode(20)
        t3 = t1 + t2
        self.assertEqual(t3.frames, 30)

    def test_subtraction(self):
        t1 = Timecode(30)
        t2 = Timecode(10)
        t3 = t1 - t2
        self.assertEqual(t3.frames, 20)
