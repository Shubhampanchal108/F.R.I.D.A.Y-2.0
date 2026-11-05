import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from dateutil import parser as dt_parser

def parse_iso_or_natural_datetime(dt_input: str) -> Optional[datetime]:
    """
    Parses flexible datetime formats including ISO-8601, 'YYYY-MM-DD HH:MM',
    or natural relative references like 'today', 'tomorrow', 'now'.
    """
    if not dt_input or not isinstance(dt_input, str):
        return None

    text = dt_input.strip()
    now = datetime.now().astimezone()

    lower = text.lower()
    if lower in ["now", "current"]:
        return now
    elif lower in ["today"]:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif lower in ["tomorrow"]:
        return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif lower in ["yesterday"]:
        return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    # Check for relative day prefix: today/tomorrow/yesterday [at] <time>
    rel_match = re.match(r"^(today|tomorrow|yesterday)(?:\s+at|\s+)?\s+(.+)$", lower)
    if rel_match:
        day_word, time_part = rel_match.groups()
        base_day = now if day_word == "today" else (now + timedelta(days=1) if day_word == "tomorrow" else now - timedelta(days=1))
        try:
            parsed_time = dt_parser.parse(time_part).time()
            return base_day.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=parsed_time.second, microsecond=0)
        except Exception:
            pass

    # Try standard dateutil parser
    try:
        parsed = dt_parser.parse(text)
        if parsed.tzinfo is None:
            # Assume local timezone
            parsed = parsed.astimezone()
        return parsed
    except Exception:
        pass

    return None


def format_rfc3339(dt: datetime) -> str:
    """Formats datetime to RFC 3339 / ISO-8601 string required by Google Calendar API."""
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt.isoformat()


def format_event_summary(event: dict) -> dict:
    """Converts a raw Google Calendar event resource into a clean, human & LLM-friendly dict."""
    start = event.get("start", {})
    end = event.get("end", {})

    start_str = start.get("dateTime") or start.get("date") or "N/A"
    end_str = end.get("dateTime") or end.get("date") or "N/A"

    attendees_list = [
        att.get("email") for att in event.get("attendees", []) if att.get("email")
    ]

    return {
        "id": event.get("id"),
        "summary": event.get("summary", "Untitled Event"),
        "start": start_str,
        "end": end_str,
        "location": event.get("location", ""),
        "description": event.get("description", ""),
        "status": event.get("status", "confirmed"),
        "htmlLink": event.get("htmlLink", ""),
        "attendees": attendees_list,
        "is_recurring": bool(event.get("recurrence"))
    }

