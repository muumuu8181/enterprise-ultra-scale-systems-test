import re

class Timecode:
    """
    A utility class for SMPTE Timecode handling.
    Defaults to 30fps (Non-Drop Frame) for this system prototype.
    """
    def __init__(self, time_str_or_frames, fps=30):
        self.fps = fps
        if isinstance(time_str_or_frames, int):
            self.frames = time_str_or_frames
        elif isinstance(time_str_or_frames, str):
            self.frames = self.time_to_frames(time_str_or_frames)
        else:
            raise ValueError("Timecode must be int (frames) or str (HH:MM:SS:FF)")

    def time_to_frames(self, time_str):
        # Format HH:MM:SS:FF or HH:MM:SS;FF
        parts = re.split(r'[:;]', time_str)
        if len(parts) != 4:
            raise ValueError("Invalid timecode format. Use HH:MM:SS:FF")

        hh, mm, ss, ff = map(int, parts)
        return (hh * 3600 * self.fps) + (mm * 60 * self.fps) + (ss * self.fps) + ff

    def __str__(self):
        total_frames = abs(self.frames) # Handle negative frames safely for display if needed
        ff = total_frames % self.fps
        total_seconds = total_frames // self.fps
        ss = total_seconds % 60
        total_minutes = total_seconds // 60
        mm = total_minutes % 60
        hh = total_minutes // 60

        sign = "-" if self.frames < 0 else ""
        return f"{sign}{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"

    def __repr__(self):
        return f"<Timecode frames={self.frames} fps={self.fps}>"

    def __add__(self, other):
        if isinstance(other, Timecode):
            if other.fps != self.fps:
                 raise ValueError("Cannot add Timecodes with different frame rates")
            return Timecode(self.frames + other.frames, self.fps)
        if isinstance(other, int):
            return Timecode(self.frames + other, self.fps)
        raise TypeError(f"Unsupported operand type for +: {type(other)}")

    def __sub__(self, other):
        if isinstance(other, Timecode):
            if other.fps != self.fps:
                 raise ValueError("Cannot subtract Timecodes with different frame rates")
            return Timecode(self.frames - other.frames, self.fps)
        if isinstance(other, int):
            return Timecode(self.frames - other, self.fps)
        raise TypeError(f"Unsupported operand type for -: {type(other)}")

    def __eq__(self, other):
         if isinstance(other, Timecode):
            return self.frames == other.frames and self.fps == other.fps
         return False

    def __lt__(self, other):
        if isinstance(other, Timecode):
             return self.frames < other.frames
        return self.frames < other

    def __gt__(self, other):
        if isinstance(other, Timecode):
             return self.frames > other.frames
        return self.frames > other
