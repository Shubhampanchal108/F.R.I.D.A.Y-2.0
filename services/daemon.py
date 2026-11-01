"""
=============================================================================
F.R.I.D.A.Y 2.0 // AUTONOMOUS SENTINEL DAEMON ORCHESTRATOR
=============================================================================
Modular orchestrator for background watchdog sentinels:
- BatterySentinel: Charging, power loss, low battery dimming
- SystemSentinel: High CPU utilization & RAM consumption
- EmailSentinel: New unread email detection
- CareSentinel: Health, posture, hydration, late-night check-ins
- ReminderSentinel: Due reminders & proactive memory recalls
- ClipboardSentinel: Code traceback & exception watcher
- BriefingService: Morning executive briefing
- NotificationEngine: Desktop toasts, Live relay, LLM speech synthesis
=============================================================================
"""

import threading
import time
import os
import sys

# Ensure UTF-8 output encoding for Windows terminal compatibility
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.notifier import NotificationEngine
from services.battery_sentinel import BatterySentinel
from services.system_sentinel import SystemSentinel
from services.email_sentinel import EmailSentinel
from services.care_sentinel import CareSentinel
from services.reminder_sentinel import ReminderSentinel
from services.clipboard_sentinel import ClipboardSentinel
from services.briefing_service import BriefingService


class FridayDaemon:
    """
    F.R.I.D.A.Y Autonomous Proactive Sentinel & Personal Secretary Daemon.
    Coordinates all modular sentinels within a single background thread.
    """

    def __init__(self, check_interval=15, notify_voice=True, on_event_callback=None):
        self.check_interval = check_interval
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()

        # Centralized Notification Engine
        self.notifier = NotificationEngine(
            notify_voice=notify_voice,
            on_event_callback=on_event_callback
        )

        # Modular Sentinels
        self.battery_sentinel = BatterySentinel(self.notifier)
        self.system_sentinel = SystemSentinel(self.notifier)
        self.email_sentinel = EmailSentinel(self.notifier)
        self.care_sentinel = CareSentinel(self.notifier)
        self.reminder_sentinel = ReminderSentinel(self.notifier)
        self.clipboard_sentinel = ClipboardSentinel(self.notifier)
        self.briefing_service = BriefingService(self.notifier)

    # --- Backward-Compatible Properties ---
    @property
    def notification_history(self):
        return self.notifier.notification_history

    @property
    def notify_voice(self):
        return self.notifier.notify_voice

    @notify_voice.setter
    def notify_voice(self, value):
        self.notifier.notify_voice = bool(value)

    @property
    def on_event_callback(self):
        return self.notifier.on_event_callback

    @on_event_callback.setter
    def on_event_callback(self, cb):
        self.notifier.on_event_callback = cb

    @property
    def is_authenticated(self):
        return self.notifier.is_authenticated

    @is_authenticated.setter
    def is_authenticated(self, value):
        self.notifier.is_authenticated = bool(value)

    def set_authenticated(self, authenticated: bool):
        """Sets authentication clearance for the daemon and centralized speech manager."""
        self.is_authenticated = bool(authenticated)
        try:
            from voice.speak import set_authenticated as speak_set_auth
            speak_set_auth(self.is_authenticated)
        except Exception:
            pass

    def record_user_activity(self):
        """Call this whenever the user interacts with Friday via voice or text."""
        self.care_sentinel.record_user_activity()

    def send_desktop_notification(self, title: str, message: str):
        self.notifier.send_desktop_notification(title, message)

    def get_recent_alerts(self, limit=5):
        """Returns the most recent proactive alerts and notifications for LLM awareness."""
        return self.notifier.notification_history[-limit:] if self.notifier.notification_history else []

    def trigger_morning_briefing(self) -> str:
        """Generates and announces a proactive morning briefing for Shubham sir."""
        return self.briefing_service.trigger_morning_briefing()

    def _loop(self):
        self.notifier.log_event("Daemon Started", "Proactive Secretary & System Sentinel active.")
        cycle_count = 0

        # Prime CPU monitor
        self.system_sentinel.prime()

        while not self._stop_event.is_set():
            cycle_count += 1

            # 1. System Reminders
            self.reminder_sentinel.check_due_reminders()

            # 2. Battery Sentinel (every cycle, 15s)
            self.battery_sentinel.check()

            # 3. CPU & RAM Performance Sentinel (every cycle, 15s)
            self.system_sentinel.check()

            # 4. Incoming Email Sentinel (every ~45s)
            self.email_sentinel.check()

            # 5. Secretary Care Check-ins (proactive Jarvis interactivity)
            self.care_sentinel.check()

            # 6. Clipboard Intelligence Sentinel (detects code errors in clipboard)
            self.clipboard_sentinel.check()

            # 7. Proactive Memory Surfacing every ~5 minutes (20 cycles at 15s)
            if cycle_count % 20 == 0:
                self.reminder_sentinel.check_proactive_memories()

            # Wait for next check interval or until stopped
            self._stop_event.wait(self.check_interval)

        self.notifier.log_event("Daemon Stopped", "Background monitoring terminated.")

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
        try:
            from Tools.Mobile_Automation import stop_mobile_keepalive_daemon
            stop_mobile_keepalive_daemon()
        except Exception:
            pass
        return True

    def is_running(self):
        return self._running and self._thread is not None and self._thread.is_alive()


# Shared singleton instance
daemon_instance = FridayDaemon()
SentinelDaemon = FridayDaemon


def get_daemon():
    global daemon_instance
    return daemon_instance


if __name__ == "__main__":
    print("Testing Modular F.R.I.D.A.Y Autonomous Sentinel Daemon...")
    d = FridayDaemon(check_interval=2, notify_voice=False)
    d.start()
    print("Daemon running for 5s (Battery, CPU, Email, Secretary Sentinel active)...")
    time.sleep(5)
    d.stop()
    print("Daemon test complete successfully.")
    print("History:", d.notification_history)
