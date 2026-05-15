from Tools.weather import get_current_weather
from Tools.systems_tools import *
from Tools.News import get_latest_news
from Tools.wikipedia import search_wikipedia
from Tools.pywhatkit import play_youtube
from Tools.Emails import check_new_mail, send_email, read_latest_emails, readmail_Full_body
from Tools.Date_Time import get_date_with_day, get_current_time
from Tools.Media_Tools import *
from Tools.Todo import add_task, list_tasks, delete_task, complete_task
from Tools.reminder import add_reminder, list_reminders, delete_reminder_by_name, get_due_reminders
from Tools.website_opner import open_website
from Tools.File_manger import *
from Tools.Mobile_Automation import (
    check_connection_json,
    connect_mobile_with_bat,
    unlock_device,
    send_whatsapp_message,
    phone_call_with_mobile
)
from Tools.browser import google_search, summrize_url 
from RAG import save_longterm_memory


# ================================
# Access Control Lists
# ================================

MOBILE_ALLOWED = {
    "get_weather",
    "get_current_time",
    "get_date_with_day",
    "check_connection_json",
    "send_whatsapp_message",
    "phone_call_with_mobile",
    "get_News",
    "search_wikipedia",
    "google_search",
    "add_reminder",
    "list_reminders",
    "delete_reminder_by_name",
    "get_due_reminders",
    "send_email",
    "add_task",
    "list_tasks",
    "delete_task",
    "complete_task",
    "read_latest_emails",
    "readmail_Full_body",
    "save_longterm_memory",
    "summrize_url",
    "check_new_mail"
}

WEB_ALLOWED = {
    "get_weather",
    "get_News",
    "search_wikipedia",
    "google_search",
    "find_my_ip",
    "get_current_time",
    "get_date_with_day",
    "open_website",
    "add_reminder",
    "list_reminders",
    "delete_reminder_by_name",
    "get_due_reminders",
    "send_email",
    "add_task",
    "list_tasks",
    "delete_task",
    "complete_task",
    "read_latest_emails",
    "readmail_Full_body",
    "save_longterm_memory",
    "summrize_url",
    "check_new_mail"
}


# ================================
# Tool Registry
# ================================

class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name, func):
        self._tools[name] = func

    def get(self, name):
        return self._tools.get(name)

    def is_allowed(self, tool_name, origin):

        # Server gets full access
        if origin.lower() == "server":
            return True

        if origin.lower() == "mobile":
            if(tool_name in MOBILE_ALLOWED):
                return True

        if origin.lower() == "web":
            if(tool_name in WEB_ALLOWED):
                return True

        return False


registry = ToolRegistry()


# ================================
# Tool Loader
# ================================

TOOLS = {
        # ---- General ----
        "get_weather": get_current_weather,
        "get_News": get_latest_news,
        "check_battery": get_battery_status,
        "search_wikipedia": search_wikipedia,
        "google_search": google_search,
        "find_my_ip": find_my_ip,
        "get_current_time": get_current_time,
        "get_date_with_day": get_date_with_day,
        "read_latest_emails": read_latest_emails,
        "readmail_Full_body": readmail_Full_body,
        "save_longterm_memory": save_longterm_memory,
        "check_new_mail": check_new_mail,

        # ---- System ----
        "open_app": open_application,
        "close_app": close_app,
        "clear_recycle_bin": empty_recycle_bin,
        "brightness_down": brightness_down,
        "brightness_up": brightness_up,
        "volume_down": volume_down,
        "volume_up": volume_up,
        "mute_volume": mute_volume,
        "unmute_volume": unmute_volume,
        "capture_screenshot": capture_screenshot,
        "minimize_active_window": minimize_active_window,
        "maximize_active_window": maximize_active_window,

        # ---- YouTube ----
        "youtube_automation": play_youtube,
        "yt_play_pause": yt_play_pause,
        "yt_next": yt_next,
        "yt_previous": yt_previous,
        "yt_fullscreen": yt_fullscreen,

        # ---- Tasks ----
        "add_task": add_task,
        "list_tasks": list_tasks,
        "delete_task": delete_task,
        "complete_task": complete_task,

        # ---- Reminders ----
        "add_reminder": add_reminder,
        "list_reminders": list_reminders,
        "delete_reminder_by_name": delete_reminder_by_name,
        "get_due_reminders": get_due_reminders,

        # ---- Files ----
        "create_and_open_file": create_and_open_file,
        "read_file": read_file,
        "update_file": update_file,
        "delete_file": delete_file,
        "list_files": list_files,
        "rename_file": rename_file,
        "search_file_in_folder": search_file_in_folder,

        # ---- Web ----
        "open_website": open_website,
        "send_email": send_email,
        "summrize_url": summrize_url,

        # ---- Mobile ----
        "connect_mobile_with_bat": connect_mobile_with_bat,
        "check_connection_json": check_connection_json,
        "unlock_device": unlock_device,
        "send_whatsapp_message": send_whatsapp_message,
        "phone_call_with_mobile": phone_call_with_mobile,
    }


def load_tools():
    for name, func in TOOLS.items():
        registry.register(name, func)

    return registry


# ================================
# Execution Layer
# ================================

def execute_tool(tool_name, origin, **kwargs):

    tool = registry.get(tool_name)

    if not tool:
        return "❌ Tool not found."

    if not registry.is_allowed(tool_name, origin):
        return f"🚫 {tool_name} not allowed for {origin}"

    try:
        return tool(**kwargs)
    except Exception as e:
        return f"⚠ Error executing tool: {str(e)}"