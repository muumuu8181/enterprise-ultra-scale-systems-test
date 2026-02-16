from django.test import TestCase
from .models import DailySchedule, PlaylistItem
from .services import ScheduleValidator
from datetime import date

class ScheduleValidatorTests(TestCase):
    def setUp(self):
        self.schedule = DailySchedule.objects.create(date=date(2023, 10, 27))

    def test_overlap_detection(self):
        # Item 1: 00:00:00:00 - 00:00:10:00 (300 frames)
        PlaylistItem.objects.create(
            schedule=self.schedule,
            start_time_frames=0,
            duration_frames=300,
            title_override="Item 1"
        )
        # Item 2: starts at 00:00:05:00 (150 frames) - Overlaps!
        PlaylistItem.objects.create(
            schedule=self.schedule,
            start_time_frames=150,
            duration_frames=300,
            title_override="Item 2"
        )

        validator = ScheduleValidator(self.schedule)
        errors = validator.validate()

        self.assertTrue(any(e['type'] == 'OVERLAP' for e in errors))

    def test_gap_detection(self):
        # Item 1: 00:00:00:00 - 00:00:10:00 (300 frames)
        PlaylistItem.objects.create(
            schedule=self.schedule,
            start_time_frames=0,
            duration_frames=300,
            title_override="Item 1"
        )
        # Item 2: starts at 00:00:20:00 (600 frames) - Gap of 300 frames
        PlaylistItem.objects.create(
            schedule=self.schedule,
            start_time_frames=600,
            duration_frames=300,
            title_override="Item 2"
        )

        validator = ScheduleValidator(self.schedule)
        errors = validator.validate()

        self.assertTrue(any(e['type'] == 'GAP' for e in errors))

    def test_no_errors(self):
        # Item 1: 00:00:00:00 - 00:00:10:00
        PlaylistItem.objects.create(
            schedule=self.schedule,
            start_time_frames=0,
            duration_frames=300,
            title_override="Item 1"
        )
        # Item 2: starts exactly at 300
        PlaylistItem.objects.create(
            schedule=self.schedule,
            start_time_frames=300,
            duration_frames=300,
            title_override="Item 2"
        )

        validator = ScheduleValidator(self.schedule)
        errors = validator.validate()

        self.assertEqual(len(errors), 0)
