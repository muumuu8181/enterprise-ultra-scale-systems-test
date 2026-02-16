from .models import DailySchedule, PlaylistItem

class ScheduleValidator:
    def __init__(self, schedule):
        self.schedule = schedule

    def validate(self):
        """
        Validates the schedule for overlaps and gaps.
        Returns a list of errors (dicts).
        """
        errors = []
        # Ensure we fetch items in order
        items = self.schedule.items.all().order_by('start_time_frames')

        last_end_time = 0
        last_item = None

        for item in items:
            start = item.start_time_frames
            end = item.start_time_frames + item.duration_frames

            # Check overlap with previous item
            if last_item and start < last_end_time:
                errors.append({
                    'type': 'OVERLAP',
                    'item_id': item.id,
                    'prev_item_id': last_item.id,
                    'overlap_frames': last_end_time - start,
                    'message': f"Item {item.id} overlaps with previous item {last_item.id} by {last_end_time - start} frames."
                })

            # Check gap
            if last_item and start > last_end_time:
                 errors.append({
                    'type': 'GAP',
                    'item_id': item.id,
                    'prev_item_id': last_item.id,
                    'gap_frames': start - last_end_time,
                    'message': f"Gap of {start - last_end_time} frames before item {item.id}."
                })

            last_end_time = end
            last_item = item

        return errors
