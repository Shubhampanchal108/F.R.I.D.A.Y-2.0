import json
import os
from datetime import datetime
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from path import DOCS_PATH


FILE = os.path.join(DOCS_PATH, "reminder.json")

# ------------------ FILE HELPERS ------------------

def _init_file():
    if not os.path.exists(FILE):
        with open(FILE, "w") as f:
            json.dump({"reminders": []}, f, indent=4)

def _load_data():
    try:
        _init_file()
        with open(FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        return {"__error__": str(e)}

def _save_data(data):
    try:
        with open(FILE, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except:
        return False

import re
from datetime import timedelta

def normalize_remind_time(time_str: str) -> str:
    """
    Parses natural language and standard time strings into 'YYYY-MM-DD HH:MM'.
    Supports:
    - 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DDTHH:MM'
    - 'tomorrow at 8 PM', 'tomorrow 9 am'
    - 'today at 5 PM', '5 PM', '17:00'
    - 'in 30 minutes', 'in 2 hours'
    """
    if not time_str:
        return ""
    s = str(time_str).strip()

    # 1. Standard ISO formats
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M", "%d-%m-%Y %H:%M"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass

    now = datetime.now()
    s_lower = s.lower().replace("at ", " ").strip()

    # 2. Relative "in X minutes" / "in X hours"
    m_rel = re.search(r'in\s+(\d+)\s*(min|minute|minutes|hr|hour|hours)', s_lower)
    if m_rel:
        num = int(m_rel.group(1))
        unit = m_rel.group(2)
        delta = timedelta(minutes=num) if "min" in unit else timedelta(hours=num)
        return (now + delta).strftime("%Y-%m-%d %H:%M")

    # 3. "tomorrow" handling
    is_tomorrow = "tomorrow" in s_lower
    s_time = s_lower.replace("tomorrow", "").replace("today", "").strip()

    # Time parsing like "8 pm", "8:30 pm", "14:00", "9 am"
    m_time = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', s_time)
    if m_time:
        hour = int(m_time.group(1))
        minute = int(m_time.group(2)) if m_time.group(2) else 0
        meridiem = m_time.group(3)

        if meridiem == "pm" and hour < 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0

        target_date = now.date() + timedelta(days=1 if is_tomorrow else 0)
        target_dt = datetime(target_date.year, target_date.month, target_date.day, hour, minute)

        # If today was specified without 'tomorrow' and the time already passed today, push to tomorrow
        if not is_tomorrow and target_dt <= now and not ("today" in s_lower):
            target_dt += timedelta(days=1)

        return target_dt.strftime("%Y-%m-%d %H:%M")

    # Try dateutil if available
    try:
        from dateutil import parser
        dt = parser.parse(s, default=now)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass

    return ""

# ------------------ REMINDER TOOLS ------------------

def add_reminder(reminder_text: str, remind_at: str):
    """
    Add a reminder with natural language or standard datetime string.
    """
    if not reminder_text.strip():
        return {"error": "Reminder text cannot be empty"}

    normalized_at = normalize_remind_time(remind_at)
    if not normalized_at:
        return {"error": f"Invalid or unrecognized date/time: '{remind_at}'. Expected format like 'YYYY-MM-DD HH:MM' or 'tomorrow at 8 PM'."}

    data = _load_data()
    if "__error__" in data:
        return {"error": f"File read error: {data['__error__']}"}

    # Check for duplicate reminders
    for r in data["reminders"]:
        if r["reminder"].lower() == reminder_text.lower() and not r.get("done"):
            return {"error": "An active reminder with this text already exists"}

    reminder = {
        "id": len(data["reminders"]) + 1,
        "reminder": reminder_text.strip(),
        "remind_at": normalized_at,
        "done": False,
        "enabled": True,
        "created_at": datetime.now().isoformat()
    }

    data["reminders"].append(reminder)

    if not _save_data(data):
        return {"error": "Failed to save reminder"}

    return {
        "status": "success",
        "message": f"Reminder set for {normalized_at}",
        "reminder": reminder
    }

def list_reminders():
    """
    List all reminders
    """
    data = _load_data()
    if "__error__" in data:
        return {"error": f"File read error: {data['__error__']}"}

    return {
        "count": len(data["reminders"]),
        "reminders": data["reminders"]
    }

def complete_reminder_by_name(reminder_text: str):
    """
    Mark a reminder as done based on its name
    """
    data = _load_data()
    if "__error__" in data:
        return {"error": f"File read error: {data['__error__']}"}

    for r in data["reminders"]:
        if r["reminder"].lower() == reminder_text.lower():
            r["done"] = True
            if not _save_data(data):
                return {"error": "Failed to update reminder"}

            return {
                "status": "success",
                "message": f"Reminder '{reminder_text}' marked as completed",
                "reminder": r
            }

def update_reminder(old_text: str, new_text: str = None, new_remind_at: str = None):
    """
    Update reminder message or scheduled time.
    """
    data = _load_data()
    if "__error__" in data:
        return {"error": f"File read error: {data['__error__']}"}

    for r in data["reminders"]:
        if r["reminder"].lower() == old_text.lower():
            if new_text and new_text.strip():
                r["reminder"] = new_text.strip()
            if new_remind_at and new_remind_at.strip():
                norm = normalize_remind_time(new_remind_at)
                if not norm:
                    return {"error": f"Invalid date/time format: '{new_remind_at}'"}
                r["remind_at"] = norm
                r["done"] = False
            r["updated_at"] = datetime.now().isoformat()

            if not _save_data(data):
                return {"error": "Failed to update reminder"}

            return {
                "status": "success",
                "message": f"Reminder updated to '{r['reminder']}' at {r['remind_at']}",
                "reminder": r
            }

    return {"error": f"Reminder '{old_text}' not found"}

def toggle_reminder(reminder_text: str, enabled: bool = None):
    """
    Enable or disable a scheduled reminder.
    """
    data = _load_data()
    if "__error__" in data:
        return {"error": f"File read error: {data['__error__']}"}

    for r in data["reminders"]:
        if r["reminder"].lower() == reminder_text.lower():
            if enabled is not None:
                r["enabled"] = bool(enabled)
            else:
                r["enabled"] = not r.get("enabled", True)

            if not _save_data(data):
                return {"error": "Failed to toggle reminder"}

            status_str = "enabled" if r["enabled"] else "disabled"
            return {
                "status": "success",
                "message": f"Reminder '{reminder_text}' {status_str}",
                "reminder": r
            }

    return {"error": f"Reminder '{reminder_text}' not found"}

def delete_reminder_by_name(reminder_text: str):
    """
    Delete a reminder based on its name
    """
    data = _load_data()
    if "__error__" in data:
        return {"error": f"File read error: {data['__error__']}"}

    new_reminders = [r for r in data["reminders"] if r["reminder"].lower() != reminder_text.lower()]

    if len(new_reminders) == len(data["reminders"]):
        return {"error": f"Reminder '{reminder_text}' not found"}

    data["reminders"] = new_reminders

    if not _save_data(data):
        return {"error": "Failed to delete reminder"}

    return {
        "status": "success",
        "message": f"Reminder '{reminder_text}' deleted successfully"
    }

# ------------------ DUE REMINDER CHECKER ------------------

def get_due_reminders():
    due_reminders = []
    data = list_reminders()

    if "error" in data:
        print("Error reading reminders:", data["error"])
        return due_reminders

    now = datetime.now()
    for r in data["reminders"]:
        if not r.get("done") and r.get("enabled", True):
            try:
                remind_time = datetime.strptime(r["remind_at"], "%Y-%m-%d %H:%M")
                if now >= remind_time:
                    complete_reminder_by_name(r["reminder"])
                    due_reminders.append(r["reminder"])
            except Exception:
                pass

    return due_reminders

# ------------------ EXAMPLES ------------------

if __name__ == "__main__":
    print(get_due_reminders())
