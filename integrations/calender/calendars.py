import logging
from typing import Dict, Any, Optional

from integrations.calender.client import get_calendar_service, get_active_calendar_id

logger = logging.getLogger("Friday.Calendar.Calendars")


def list_user_calendars() -> Dict[str, Any]:
    """
    Lists all Google Calendars in the user's account.
    Returns calendar IDs, summary, primary flag, and access role.
    """
    service, err = get_calendar_service(interactive=False)
    if err:
        return {"status": "error", "message": err, "calendars": []}

    try:
        cal_list = service.calendarList().list().execute()
        items = cal_list.get("items", [])

        calendars = []
        for c in items:
            calendars.append({
                "id": c.get("id"),
                "summary": c.get("summary", "Untitled"),
                "description": c.get("description", ""),
                "primary": c.get("primary", False),
                "accessRole": c.get("accessRole", "reader"),
                "timeZone": c.get("timeZone", "")
            })

        return {
            "status": "success",
            "count": len(calendars),
            "calendars": calendars
        }
    except Exception as e:
        logger.error(f"Error listing calendars: {e}")
        return {"status": "error", "message": f"Failed to list calendars: {str(e)}", "calendars": []}


def get_calendar_metadata(calendar_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves details of a specific or active calendar."""
    service, err = get_calendar_service(interactive=False)
    if err:
        return {"status": "error", "message": err}

    target_id = calendar_id or get_active_calendar_id()
    try:
        cal = service.calendars().get(calendarId=target_id).execute()
        return {
            "status": "success",
            "calendar": {
                "id": cal.get("id"),
                "summary": cal.get("summary"),
                "description": cal.get("description", ""),
                "timeZone": cal.get("timeZone", "")
            }
        }
    except Exception as e:
        logger.error(f"Error fetching calendar metadata: {e}")
        return {"status": "error", "message": f"Failed to get calendar: {str(e)}"}

