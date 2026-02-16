from django.db import models
from broadcast_core.utils import Timecode

class DailySchedule(models.Model):
    """
    Represents the playlist for a specific broadcast day.
    """
    date = models.DateField(unique=True)
    is_finalized = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.date)

class PlaylistItem(models.Model):
    """
    A single item in the daily schedule.
    """
    schedule = models.ForeignKey(DailySchedule, on_delete=models.CASCADE, related_name='items')

    # Timing (in frames from 00:00:00:00 of the broadcast day)
    start_time_frames = models.PositiveIntegerField()
    # Duration (should match material but can be explicit)
    duration_frames = models.PositiveIntegerField()

    # Content (One of these should be set)
    episode = models.ForeignKey('production.Episode', on_delete=models.PROTECT, null=True, blank=True)
    commercial = models.ForeignKey('cm.Commercial', on_delete=models.PROTECT, null=True, blank=True)

    # Or filler/live segment
    title_override = models.CharField(max_length=255, blank=True, help_text="Override title or title for filler")

    class Meta:
        ordering = ['start_time_frames']

    def __str__(self):
        # Convert frames to Timecode string for display
        tc = Timecode(self.start_time_frames)
        title = self.title_override
        if not title:
            if self.episode:
                title = str(self.episode)
            elif self.commercial:
                title = str(self.commercial)
            else:
                title = "Unknown"
        return f"[{tc}] {title}"

    @property
    def end_time_frames(self):
        return self.start_time_frames + self.duration_frames
