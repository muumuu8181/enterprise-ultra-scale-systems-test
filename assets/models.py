from django.db import models

class Material(models.Model):
    """
    Represents a media asset (Program segment, CM, etc.).
    """
    FORMAT_CHOICES = [
        ('MXF', 'MXF'),
        ('MP4', 'MP4'),
        ('MOV', 'QuickTime'),
    ]

    title = models.CharField(max_length=255)
    duration_frames = models.PositiveIntegerField(help_text="Duration in frames (30fps)")
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='MXF')
    som = models.CharField(max_length=11, help_text="Start of Message Timecode (HH:MM:SS:FF)", default="00:00:00:00")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.duration_frames}f)"
