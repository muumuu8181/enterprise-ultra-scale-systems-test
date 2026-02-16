from datetime import datetime, timedelta

def get_current_15min_interval(dt: datetime = None) -> datetime:
    """Returns the start time of the current 15-minute interval."""
    if dt is None:
        dt = datetime.now()
    minute = (dt.minute // 15) * 15
    return dt.replace(minute=minute, second=0, microsecond=0)

def get_next_15min_interval(dt: datetime = None) -> datetime:
    """Returns the start time of the next 15-minute interval."""
    current = get_current_15min_interval(dt)
    return current + timedelta(minutes=15)
