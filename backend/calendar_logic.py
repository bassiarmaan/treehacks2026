"""
Calendar free-slot computation.
Merges busy intervals from all team members and finds overlapping free windows.
"""

from datetime import datetime, timedelta


def _parse_dt(s: str) -> datetime:
    """Parse an ISO datetime string."""
    # Handle multiple formats
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            continue
    # Last resort: just a date
    return datetime.strptime(s, "%Y-%m-%d")


def _format_dt(dt: datetime) -> str:
    """Format datetime for display: 'Mon Feb 17 2:00 PM'."""
    return dt.strftime("%a %b %d %-I:%M %p")


def _format_iso(dt: datetime) -> str:
    return dt.isoformat()


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Merge overlapping time intervals into non-overlapping ones."""
    if not intervals:
        return []
    sorted_ivs = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_ivs[0]]
    for start, end in sorted_ivs[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def subtract_intervals(
    free: list[tuple[datetime, datetime]],
    busy: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    """Subtract busy intervals from free intervals."""
    result = []
    busy_idx = 0
    busy_sorted = sorted(busy, key=lambda x: x[0])

    for f_start, f_end in free:
        current = f_start
        while busy_idx < len(busy_sorted) and busy_sorted[busy_idx][1] <= current:
            busy_idx += 1

        bi = busy_idx
        while bi < len(busy_sorted) and busy_sorted[bi][0] < f_end:
            b_start, b_end = busy_sorted[bi]
            if b_start > current:
                result.append((current, min(b_start, f_end)))
            current = max(current, b_end)
            bi += 1

        if current < f_end:
            result.append((current, f_end))

    return result


def find_free_slots(
    all_busy_times: list[list[dict]],
    duration_minutes: int,
    start_date: str,
    end_date: str,
    day_start_hour: int = 9,
    day_end_hour: int = 18,
) -> list[dict]:
    """
    Find free time slots where ALL team members are available.

    Args:
        all_busy_times: List of busy-time lists, one per member.
                        Each busy time is {"start": "ISO", "end": "ISO"}.
        duration_minutes: Minimum slot duration in minutes.
        start_date: Start of search range (YYYY-MM-DD).
        end_date: End of search range (YYYY-MM-DD).
        day_start_hour: Business hours start (default 9).
        day_end_hour: Business hours end (default 18).

    Returns:
        List of {"start": "ISO", "end": "ISO", "display": "formatted"} dicts.
    """
    # Parse date range
    try:
        range_start = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        range_start = _parse_dt(start_date)

    try:
        range_end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        range_end = _parse_dt(end_date)

    # Build per-day free windows (business hours)
    free_windows: list[tuple[datetime, datetime]] = []
    current_day = range_start
    while current_day <= range_end:
        day_start = current_day.replace(hour=day_start_hour, minute=0, second=0)
        day_end = current_day.replace(hour=day_end_hour, minute=0, second=0)
        # Skip weekends
        if current_day.weekday() < 5:  # Mon-Fri
            free_windows.append((day_start, day_end))
        current_day += timedelta(days=1)

    if not free_windows:
        return []

    # Merge ALL busy intervals from ALL members
    all_busy: list[tuple[datetime, datetime]] = []
    for member_busy in all_busy_times:
        for interval in member_busy:
            try:
                start = _parse_dt(interval["start"])
                end = _parse_dt(interval["end"])
                # Strip timezone for comparison if needed
                if start.tzinfo:
                    start = start.replace(tzinfo=None)
                if end.tzinfo:
                    end = end.replace(tzinfo=None)
                all_busy.append((start, end))
            except (KeyError, ValueError) as e:
                print(f"Skipping invalid interval {interval}: {e}")
                continue

    merged_busy = merge_intervals(all_busy)

    # Subtract busy from free
    available = subtract_intervals(free_windows, merged_busy)

    # Filter by minimum duration
    min_duration = timedelta(minutes=duration_minutes)
    slots = []
    for start, end in available:
        if end - start >= min_duration:
            slots.append({
                "start": _format_iso(start),
                "end": _format_iso(end),
                "display": f"{_format_dt(start)} - {_format_dt(end)}",
                "duration_minutes": int((end - start).total_seconds() / 60),
            })

    return slots
