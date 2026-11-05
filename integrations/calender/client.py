import os
import logging
from datetime import datetime
from typing import Optional, Tuple
from googleapiclient.discovery import build, Resource

from config.config_driver import load_data
from integrations.calender.auth import get_credentials

logger = logging.getLogger("Friday.Calendar.Client")

_service_cache: Optional[Resource] = None


def get_active_calendar_id() -> str:
    """Returns the user configured calendar id, defaulting to 'primary'."""
    try:
        data = load_data()
        cal_id = data.get("KEYS", {}).get("GOOGLE_CALENDAR_ID", "primary")
        if not cal_id or not str(cal_id).strip():
            return "primary"
        return str(cal_id).strip()
    except Exception:
        return "primary"


WINDOWS_TO_IANA = {
    "India Standard Time": "Asia/Kolkata",
    "IST": "Asia/Kolkata",
    "Pacific Standard Time": "America/Los_Angeles",
    "Eastern Standard Time": "America/New_York",
    "Central Standard Time": "America/Chicago",
    "Mountain Standard Time": "America/Denver",
    "GMT Standard Time": "Europe/London",
    "UTC": "UTC",
}


def get_local_timezone_str() -> str:
    """Attempts to determine local system timezone string, fallback to Asia/Kolkata or UTC."""
    try:
        local_tz = str(datetime.now().astimezone().tzinfo)
        if "/" in local_tz or local_tz == "UTC":
            return local_tz
        if local_tz in WINDOWS_TO_IANA:
            return WINDOWS_TO_IANA[local_tz]
    except Exception:
        pass
    return "Asia/Kolkata"


def get_calendar_service(interactive: bool = True) -> Tuple[Optional[Resource], Optional[str]]:
    """
    Returns (service_resource, error_message).
    If service cannot be initialized, returns (None, explanation).
    """
    global _service_cache

    try:
        creds = get_credentials(interactive=interactive)
        if not creds:
            return None, (
                "Google Calendar credentials missing or authorization incomplete. "
                "Please configure your Google Calendar Client ID and Secret in Friday UI Settings."
            )

        # Build service
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        _service_cache = service
        return service, None
    except Exception as e:
        logger.error(f"Failed to create Google Calendar service: {e}")
        return None, f"Failed to initialize Google Calendar API: {str(e)}"
