import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

FILE = os.getenv("Reminder_Path")

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

# ------------------ REMINDER TOOLS ------------------

def add_reminder(reminder_text: str, remind_at: str):
    """
    Add a reminder.
    remind_at should be in 'YYYY-MM-DD HH:MM' format
    """
    if not reminder_text.strip():
        return {"error": "Reminder text cannot be empty"}

    try:
        datetime.strptime(remind_at, "%Y-%m-%d %H:%M")
    except ValueError:
        return {"error": "Invalid date format. Use 'YYYY-MM-DD HH:MM'"}

    data = _load_data()
    if "__error__" in data:
        return {"error": f"File read error: {data['__error__']}"}

    # Check for duplicate reminders
    for r in data["reminders"]:
        if r["reminder"].lower() == reminder_text.lower():
            return {"error": "Reminder with this text already exists"}

    reminder = {
        "id": len(data["reminders"]) + 1,
        "reminder": reminder_text.strip(),
        "remind_at": remind_at,
        "done": False,
        "created_at": datetime.now().isoformat()
    }

    data["reminders"].append(reminder)

    if not _save_data(data):
        return {"error": "Failed to save reminder"}

    return {
        "status": "success",
        "message": "Reminder added successfully",
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
        if not r["done"]:
            remind_time = datetime.strptime(r["remind_at"], "%Y-%m-%d %H:%M")
            if now >= remind_time:
                complete_reminder_by_name(r["reminder"])
                due_reminders.append(r["reminder"])

    return due_reminders

# ------------------ EXAMPLES ------------------

if __name__ == "__main__":
    print(get_due_reminders())
