import threading
import time
from datetime import datetime
import os
import sys

# Ensure UTF-8 output encoding for Windows terminal compatibility
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from Tools.reminder import get_due_reminders
from speak import speak

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


class FridayDaemon:
    def __init__(self, check_interval=15, notify_voice=True, on_event_callback=None):
        self.check_interval = check_interval
        self.notify_voice = notify_voice
        self.on_event_callback = on_event_callback
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()
        self.notification_history = []

    def _log_event(self, title, message, level="INFO"):
        event = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "title": title,
            "message": message,
            "level": level
        }
        self.notification_history.append(event)
        if len(self.notification_history) > 50:
            self.notification_history.pop(0)

        if self.on_event_callback:
            try:
                self.on_event_callback(event)
            except Exception:
                pass

    def send_desktop_notification(self, title: str, message: str):
        self._log_event(title, message)
        
        # OS Desktop Notification
        if PLYER_AVAILABLE:
            try:
                notification.notify(
                    title=f"F.R.I.D.A.Y — {title}",
                    message=message,
                    app_name="FRIDAY AI Agent",
                    timeout=8
                )
            except Exception as e:
                print(f"\n[F.R.I.D.A.Y NOTIFICATION] {title}: {message}\n")
        else:
            print(f"\n[F.R.I.D.A.Y NOTIFICATION] {title}: {message}\n")

    def trigger_morning_briefing(self):
        """Generates and announces a proactive morning briefing for Shubham sir."""
        try:
            from Tools.weather import get_current_weather
            from Tools.systems_tools import get_battery_status
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

            self.send_desktop_notification("Morning Briefing", briefing_text)
            if self.notify_voice:
                speak(briefing_text)
            return briefing_text

        except Exception as e:
            err_msg = f"Briefing generation error: {e}"
            self._log_event("Briefing Error", err_msg, level="ERROR")
            return err_msg

    def _check_due_reminders(self):
        try:
            due = get_due_reminders()
            if due:
                for reminder in due:
                    title = "Reminder Alert"
                    msg = f"Sir, you asked me to remind you: '{reminder}'"
                    self.send_desktop_notification(title, msg)
                    if self.notify_voice:
                        speak(msg)
        except Exception as e:
            self._log_event("Daemon Check Error", str(e), level="ERROR")

    def _loop(self):
        self._log_event("Daemon Started", "Background monitoring active.")
        while not self._stop_event.is_set():
            self._check_due_reminders()
            # Wait for next check interval or until stopped
            self._stop_event.wait(self.check_interval)

        self._log_event("Daemon Stopped", "Background monitoring terminated.")

    def start(self):
        if self._running:
            return False
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        if not self._running:
            return False
        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        return True

    def is_running(self):
        return self._running and self._thread is not None and self._thread.is_alive()


# Shared singleton instance
daemon_instance = FridayDaemon()


if __name__ == "__main__":
    print("Testing F.R.I.D.A.Y Daemon...")
    d = FridayDaemon(check_interval=3)
    d.start()
    print("Daemon running for 5s...")
    time.sleep(5)
    d.stop()
    print("Daemon test complete successfully.")
