"""
Calendar Tool Wrapper for F.R.I.D.A.Y
Directly delegates to integrations.calender modules.
"""

from integrations.calender import (
    list_calendar_events,
    get_today_calendar_events,
    quick_add_calendar_event,
    create_calendar_event,
    update_calendar_event,
    delete_calendar_event,
    check_calendar_conflicts,
    create_recurring_calendar_event,
    list_user_calendars,
    get_calendar_metadata
)

__all__ = [
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

