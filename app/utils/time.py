"""Time manipulation and ISO 8601 formatting utilities."""

from datetime import datetime, timezone, timedelta
from typing import Optional


def now_utc() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def now_utc_iso() -> str:
    """Return ISO 8601 formatted UTC timestamp."""
    return now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(iso_str: str) -> datetime:
    """Parse ISO timestamp with fallback to UTC."""
    try:
        # Replace Z with +00:00 for fromisoformat compatibility
        clean = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return now_utc()


def get_forecast_horizon_hours(target_time: str, base_time: Optional[str] = None) -> float:
    """Calculate forecast lead time (horizon) in hours."""
    t_target = parse_iso(target_time)
    t_base = parse_iso(base_time) if base_time else now_utc()
    delta = t_target - t_base
    return max(0.0, delta.total_seconds() / 3600.0)
