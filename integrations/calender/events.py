import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union

from integrations.calender.client import (
    get_calendar_service,
    get_active_calendar_id,
    get_local_timezone_str
)
from integrations.calender.helpers import (
    parse_iso_or_natural_datetime,
    format_rfc3339,
    format_event_summary
)

logger = logging.getLogger("Friday.Calendar.Events")


def list_calendar_events(
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 10,
    calendar_id: Optional[str] = None,
    query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lists upcoming or date-filtered events from Google Calendar.
    - time_min / time_max: ISO string or natural strings like 'today', 'tomorrow', '2026-11-05'.
    - query: Optional text search filter.
    """
    service, err = get_calendar_service(interactive=False)
    if err:
        return {"status": "error", "message": err, "events": []}

    target_cal_id = calendar_id or get_active_calendar_id()

    # Default time_min to now if not provided
    dt_min = parse_iso_or_natural_datetime(time_min) if time_min else datetime.now().astimezone()
    dt_max = parse_iso_or_natural_datetime(time_max) if time_max else None

    params: Dict[str, Any] = {
        "calendarId": target_cal_id,
        "maxResults": max(1, min(max_results, 50)),
        "singleEvents": True,
        "orderBy": "startTime"
    }

    if dt_min:
        params["timeMin"] = format_rfc3339(dt_min)
    if dt_max:
        params["timeMax"] = format_rfc3339(dt_max)
    if query:
        params["q"] = str(query)

    try:
        events_result = service.events().list(**params).execute()
        raw_items = events_result.get("items", [])
        events = [format_event_summary(ev) for ev in raw_items]

        return {
            "status": "success",
            "count": len(events),
            "calendar_id": target_cal_id,
            "events": events
        }
    except Exception as e:
        logger.error(f"Error listing calendar events: {e}")
        return {"status": "error", "message": f"Calendar list failed: {str(e)}", "events": []}


def get_today_calendar_events() -> Dict[str, Any]:
    """Fetches all events scheduled for today (00:00 to 23:59:59)."""
    now = datetime.now().astimezone()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    return list_calendar_events(
        time_min=format_rfc3339(start_of_day),
        time_max=format_rfc3339(end_of_day),
        max_results=25
    )


def quick_add_calendar_event(text: str, calendar_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates an event using Google Calendar NLP parser.
    Example: quick_add_calendar_event("Appointment at Doctor tomorrow at 4pm")
    """
    if not text or not text.strip():
        return {"status": "error", "message": "Quick add text cannot be empty"}

    service, err = get_calendar_service(interactive=False)
    if err:
        return {"status": "error", "message": err}

    target_cal_id = calendar_id or get_active_calendar_id()

    try:
        created_event = service.events().quickAdd(
            calendarId=target_cal_id,
            text=text.strip()
        ).execute()

        return {
            "status": "success",
            "message": f"Event '{created_event.get('summary')}' created successfully via Quick Add",
            "event": format_event_summary(created_event)
        }
    except Exception as e:
        logger.error(f"Error in quick_add_calendar_event: {e}")
        return {"status": "error", "message": f"Quick add failed: {str(e)}"}


def create_calendar_event(
    summary: str,
    start_time: str,
    end_time: Optional[str] = None,
    duration_minutes: int = 60,
    description: str = "",
    location: str = "",
    attendees: Optional[Union[List[str], str]] = None,
    reminders_minutes: Optional[List[int]] = None,
    calendar_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a detailed Google Calendar event.
    - summary: Title of the event
    - start_time: Start datetime (e.g. '2026-11-05 15:00', ISO-8601, or 'tomorrow 10am')
    - end_time: Optional end datetime. If None, duration_minutes is used.
    - attendees: List of email strings or comma-separated string
    - reminders_minutes: List of minutes before event for popup alerts (e.g. [10, 30])
    """
    if not summary or not summary.strip():
        return {"status": "error", "message": "Event summary/title is required"}

    service, err = get_calendar_service(interactive=False)
    if err:
        return {"status": "error", "message": err}

    dt_start = parse_iso_or_natural_datetime(start_time)
    if not dt_start:
        return {"status": "error", "message": f"Could not parse start_time: '{start_time}'"}

    if end_time:
        dt_end = parse_iso_or_natural_datetime(end_time)
        if not dt_end:
            dt_end = dt_start + timedelta(minutes=duration_minutes)
    else:
        dt_end = dt_start + timedelta(minutes=duration_minutes)

    target_cal_id = calendar_id or get_active_calendar_id()
    tz_str = get_local_timezone_str()

    event_body: Dict[str, Any] = {
        "summary": summary.strip(),
        "description": description.strip() if description else "",
        "location": location.strip() if location else "",
        "start": {
            "dateTime": format_rfc3339(dt_start),
            "timeZone": tz_str
        },
        "end": {
            "dateTime": format_rfc3339(dt_end),
            "timeZone": tz_str
        }
    }

    # Format attendees
    if attendees:
        if isinstance(attendees, str):
            attendees = [a.strip() for a in attendees.split(",") if a.strip()]
        event_body["attendees"] = [{"email": a} for a in attendees]

    # Format reminders
    if reminders_minutes:
        overrides = [{"method": "popup", "minutes": m} for m in reminders_minutes]
        event_body["reminders"] = {
            "useDefault": False,
            "overrides": overrides
        }
    else:
        event_body["reminders"] = {"useDefault": True}

    try:
        created_event = service.events().insert(
            calendarId=target_cal_id,
            body=event_body
        ).execute()

        return {
            "status": "success",
            "message": f"Event '{summary}' successfully scheduled for {dt_start.strftime('%Y-%m-%d %H:%M')}",
            "event": format_event_summary(created_event)
        }
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        return {"status": "error", "message": f"Failed to create event: {str(e)}"}


def update_calendar_event(
    event_id: str,
    summary: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    calendar_id: Optional[str] = None
) -> Dict[str, Any]:
    """Updates an existing calendar event by event_id."""
    if not event_id:
        return {"status": "error", "message": "event_id is required"}

    service, err = get_calendar_service(interactive=False)
    if err:
        return {"status": "error", "message": err}

    target_cal_id = calendar_id or get_active_calendar_id()

    try:
        # Get existing event
        event = service.events().get(calendarId=target_cal_id, eventId=event_id).execute()

        if summary:
            event["summary"] = summary.strip()
        if description is not None:
            event["description"] = description.strip()
        if location is not None:
            event["location"] = location.strip()

        tz_str = get_local_timezone_str()
        if start_time:
            dt_s = parse_iso_or_natural_datetime(start_time)
            if dt_s:
                event["start"] = {"dateTime": format_rfc3339(dt_s), "timeZone": tz_str}
        if end_time:
            dt_e = parse_iso_or_natural_datetime(end_time)
            if dt_e:
                event["end"] = {"dateTime": format_rfc3339(dt_e), "timeZone": tz_str}

        updated = service.events().update(
            calendarId=target_cal_id,
            eventId=event_id,
            body=event
        ).execute()

        return {
            "status": "success",
            "message": f"Event '{updated.get('summary')}' successfully updated",
            "event": format_event_summary(updated)
        }
    except Exception as e:
        logger.error(f"Error updating calendar event {event_id}: {e}")
        return {"status": "error", "message": f"Failed to update event: {str(e)}"}


def delete_calendar_event(
    event_id: Optional[str] = None,
    summary_query: Optional[str] = None,
    calendar_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Deletes an event from Google Calendar.
    Can be deleted directly using event_id OR by searching summary_query.
    """
    service, err = get_calendar_service(interactive=False)
    if err:
        return {"status": "error", "message": err}

    target_cal_id = calendar_id or get_active_calendar_id()

    try:
        target_id = event_id

        # If event_id not supplied, search by summary_query
        if not target_id:
            if not summary_query:
                return {"status": "error", "message": "Either event_id or summary_query must be provided to delete."}

            search_res = list_calendar_events(query=summary_query, max_results=5, calendar_id=target_cal_id)
            events = search_res.get("events", [])
            if not events:
                return {"status": "error", "message": f"No event found matching '{summary_query}'"}
            target_id = events[0].get("id")
            summary_name = events[0].get("summary")
        else:
            summary_name = target_id

        service.events().delete(calendarId=target_cal_id, eventId=target_id).execute()
        return {
            "status": "success",
            "message": f"Event '{summary_name}' has been successfully deleted from your calendar."
        }
    except Exception as e:
        logger.error(f"Error deleting calendar event: {e}")
        return {"status": "error", "message": f"Failed to delete event: {str(e)}"}


def check_calendar_conflicts(
    start_time: str,
    end_time: Optional[str] = None,
    duration_minutes: int = 60,
    calendar_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Queries Google Calendar FreeBusy API to determine if the user has scheduling conflicts.
    Returns status: 'free' or 'busy' with overlapping event times.
    """
    service, err = get_calendar_service(interactive=False)
    if err:
        return {"status": "error", "message": err}

    dt_start = parse_iso_or_natural_datetime(start_time)
    if not dt_start:
        return {"status": "error", "message": f"Invalid start_time: {start_time}"}

    dt_end = parse_iso_or_natural_datetime(end_time) if end_time else (dt_start + timedelta(minutes=duration_minutes))
    target_cal_id = calendar_id or get_active_calendar_id()

    try:
        body = {
            "timeMin": format_rfc3339(dt_start),
            "timeMax": format_rfc3339(dt_end),
            "items": [{"id": target_cal_id}]
        }

        fb_result = service.freebusy().query(body=body).execute()
        calendars = fb_result.get("calendars", {})
        busy_slots = calendars.get(target_cal_id, {}).get("busy", [])

        if not busy_slots:
            return {
                "status": "success",
                "availability": "free",
                "message": f"You are completely free between {dt_start.strftime('%I:%M %p')} and {dt_end.strftime('%I:%M %p')}.",
                "conflicts": []
            }
        else:
            return {
                "status": "success",
                "availability": "busy",
                "message": f"Conflict detected! You have {len(busy_slots)} overlapping commitment(s) in this time slot.",
                "conflicts": busy_slots
            }
    except Exception as e:
        logger.error(f"Error checking calendar conflicts: {e}")
        return {"status": "error", "message": f"Failed to check conflicts: {str(e)}"}


def create_recurring_calendar_event(
    summary: str,
    start_time: str,
    duration_minutes: int = 60,
    freq: str = "WEEKLY",
    count: int = 10,
    description: str = "",
    location: str = "",
    calendar_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a recurring event (DAILY, WEEKLY, MONTHLY) using RRULE.
    - freq: 'DAILY' | 'WEEKLY' | 'MONTHLY'
    - count: Number of occurrences (default 10)
    """
    service, err = get_calendar_service(interactive=False)
    if err:
        return {"status": "error", "message": err}

    dt_start = parse_iso_or_natural_datetime(start_time)
    if not dt_start:
        return {"status": "error", "message": f"Invalid start_time: {start_time}"}

    dt_end = dt_start + timedelta(minutes=duration_minutes)
    target_cal_id = calendar_id or get_active_calendar_id()
    tz_str = get_local_timezone_str()

    rule = f"RRULE:FREQ={freq.upper()};COUNT={max(1, count)}"

    event_body = {
        "summary": summary.strip(),
        "description": description.strip() if description else "",
        "location": location.strip() if location else "",
        "start": {"dateTime": format_rfc3339(dt_start), "timeZone": tz_str},
        "end": {"dateTime": format_rfc3339(dt_end), "timeZone": tz_str},
        "recurrence": [rule]
    }

    try:
        created = service.events().insert(calendarId=target_cal_id, body=event_body).execute()
        return {
            "status": "success",
            "message": f"Recurring event '{summary}' scheduled successfully ({freq.lower()} for {count} occurrences).",
            "event": format_event_summary(created)
        }
    except Exception as e:
        logger.error(f"Error creating recurring event: {e}")
        return {"status": "error", "message": f"Failed to create recurring event: {str(e)}"}

if __name__ == "__main__":
    print(quick_add_calendar_event(text= "Testing Inigration"))