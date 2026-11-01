import os
import sys

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools.systems_tools import get_battery_status


class BriefingService:
    """
    Generates and announces proactive morning briefings for Shubham sir,
    including battery health, pending reminders, and weather.
    """

    def __init__(self, notifier):
        self.notifier = notifier

    def trigger_morning_briefing(self) -> str:
        """Generates and announces a proactive morning briefing for Shubham sir."""
        try:
            from Tools.weather import get_current_weather
            from Tools.reminder import list_reminders

            batt = get_battery_status()
            batt_pct = batt.get("battery_percentage", "N/A") if isinstance(batt, dict) else "N/A"

            rem_data = list_reminders()
            rems = rem_data.get("reminders", []) if isinstance(rem_data, dict) else []
            pending_count = sum(1 for r in rems if not r.get("done"))

            weather_res = get_current_weather("Kaithal")
            weather_desc = weather_res.get("weather", "clear") if isinstance(weather_res, dict) else "clear"
            temp = weather_res.get("temperature", "24°C") if isinstance(weather_res, dict) else "24°C"

            briefing_text = (
                f"Good day Shubham Sir! Here is your proactive briefing: "
                f"Weather in Kaithal is {weather_desc} at {temp}. "
                f"Your laptop battery is at {batt_pct} percent. "
                f"You have {pending_count} pending reminders today."
            )

            self.notifier.announce("Morning Briefing", briefing_text, briefing_text)
            return briefing_text

        except Exception as e:
            err_msg = f"Briefing generation error: {e}"
            self.notifier.log_event("Briefing Error", err_msg, level="ERROR")
            return err_msg

