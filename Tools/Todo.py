import json
import os
from datetime import datetime

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from path import  DOCS_PATH


FILE = os.path.join(DOCS_PATH, "todo.json")

# ------------------ FILE HELPERS ------------------

def _init_file():
    if not os.path.exists(FILE):
        with open(FILE, "w") as f:
            json.dump({"tasks": []}, f, indent=4)

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

# ------------------ TASK TOOLS ------------------

def add_task(task_text: str):
    if not task_text.strip():
        return {"error": "Task text cannot be empty"}

    data = _load_data()
    if "__error__" in data:
        return {"error": f"File read error: {data['__error__']}"}

    # Check for duplicate task names
    for t in data["tasks"]:
        if t["task"].lower() == task_text.lower():
            return {"error": "Task with this name already exists"}

    task = {
        "id": len(data["tasks"]) + 1,
        "task": task_text.strip(),
        "done": False,
        "created_at": datetime.now().isoformat()
    }

    data["tasks"].append(task)

    if not _save_data(data):
        return {"error": "Failed to save task"}

    return {
        "status": "success",
        "message": "Task added successfully",
        "task": task
    }

def list_tasks():
    data = _load_data()
    if "__error__" in data:
        return {"error": f"File read error: {data['__error__']}"}

    return {
        "count": len(data["tasks"]),
        "tasks": data["tasks"]
    }

def complete_task(task_name: str):
    data = _load_data()
    if "__error__" in data:
        return {"error": f"File read error: {data['__error__']}"}

    for task in data["tasks"]:
        if task["task"].lower() == task_name.lower():  # case-insensitive
            task["done"] = True

            if not _save_data(data):
                return {"error": "Failed to update task"}

            return {
                "status": "success",
                "message": f"Task '{task_name}' marked as completed",
                "task": task
            }

    return {"error": f"Task with name '{task_name}' not found"}

def delete_task(task_name: str):
    data = _load_data()
    if "__error__" in data:
        return {"error": f"File read error: {data['__error__']}"}

    new_tasks = [t for t in data["tasks"] if t["task"].lower() != task_name.lower()]

    if len(new_tasks) == len(data["tasks"]):
        return {"error": f"Task with name '{task_name}' not found"}

    data["tasks"] = new_tasks

    if not _save_data(data):
        return {"error": "Failed to delete task"}

    return {
        "status": "success",
        "message": f"Task '{task_name}' deleted successfully"
    }

