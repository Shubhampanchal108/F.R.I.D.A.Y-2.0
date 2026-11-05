"""
Google Calendar Complete Integration for F.R.I.D.A.Y
Exposes all calendar operations for tool guard, AI planner, and live modes.
"""

from integrations.calender.auth import get_credentials, get_client_config
from integrations.calender.client import get_calendar_service, get_active_calendar_id
from integrations.calender.events import (
    list_calendar_events,
    get_today_calendar_events,
    quick_add_calendar_event,
    create_calendar_event,
    update_calendar_event,
    delete_calendar_event,
    check_calendar_conflicts,
    create_recurring_calendar_event
)
from integrations.calender.calendars import (
    list_user_calendars,
    get_calendar_metadata
)

__all__ = [
    "get_credentials",
    "get_client_config",
    "get_calendar_service",
    "get_active_calendar_id",
    "list_calendar_events",
    "get_today_calendar_events",
    "quick_add_calendar_event",
    "create_calendar_event",
    "update_calendar_event",
    "delete_calendar_event",
    "check_calendar_conflicts",
    "create_recurring_calendar_event",
    "list_user_calendars",
    "get_calendar_metadata"
]

