import threading
import time
from datetime import datetime
import os
import sys
import json

# Ensure UTF-8 output encoding for Windows terminal compatibility
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from Tools.reminder import get_due_reminders
from Tools.systems_tools import get_battery_status, get_cpu_status, get_top_resource_consumers
from Tools.Emails import check_new_mail
from voice.speak import speak, is_speaking

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

# Suppress noisy plyer balloon_tip thread errors on Windows if tray icon is unavailable
def _suppress_plyer_thread_err(args):
    if "balloon_tip" in str(args.exc_value) or "Shell_NotifyIconW" in str(args.exc_value):
        return
    if sys.__excepthook__:
        try:
            sys.__excepthook__(args.exc_type, args.exc_value, args.exc_traceback)
        except Exception:
            pass

if hasattr(threading, "excepthook"):
    threading.excepthook = _suppress_plyer_thread_err


class FridayDaemon:
    """
    F.R.I.D.A.Y Autonomous Proactive Sentinel & Personal Secretary Daemon.
    
    Continuously monitors in the background:
    1. System Health: Battery levels (charging, unplugged, critical low, full charge), CPU & RAM spikes.
    2. Communication: Real-time incoming email notifications (sender & subject).
    3. Personal Secretary Care: Reminders, health/break check-ins (Jarvis-style), memory surfacing.
    """

    def __init__(self, check_interval=15, notify_voice=True, on_event_callback=None):
        self.check_interval = check_interval
        self.notify_voice = notify_voice
        self.on_event_callback = on_event_callback
        self.is_authenticated = False
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()
        self.notification_history = []

        # --- Battery Sentinel State ---
        self._last_plugged = None
        self._last_battery_pct = None
        self._battery_alert_state = None  # None | "low" | "critical"
        self._full_battery_alerted = False

        # --- CPU & RAM Sentinel State ---
        self._high_cpu_count = 0
        self._last_cpu_alert_time = 0
        self._last_ram_alert_time = 0
        self.cpu_threshold = 85.0
        self.cpu_cooldown = 300.0  # 5 minutes
        self.ram_threshold = 92.0
        self.ram_cooldown = 600.0  # 10 minutes

        # --- Email Sentinel State ---
        self._seen_email_ids = set()
        self._last_email_check = 0
        self.email_check_interval = 45.0  # seconds

        # --- Secretary Care & Idle Check-in State ---
        self.last_user_activity = time.time()
        self.last_care_checkin = time.time()
        self.care_interval = 2700.0  # 45 minutes
        self._care_prompt_index = 0

        # --- Clipboard Sentinel State ---
        self._last_clipboard_text = ""
        self._last_clipboard_time = 0

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
        self.last_user_activity = time.time()

    def _log_event(self, title, message, level="INFO"):
        event = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "title": title,
            "message": message,
            "level": level
        }
        self.notification_history.append(event)
        if len(self.notification_history) > 60:
            self.notification_history.pop(0)

        if self.on_event_callback:
            try:
                self.on_event_callback(event)
            except Exception:
                pass

    def send_desktop_notification(self, title: str, message: str):
        self._log_event(title, message)
        if PLYER_AVAILABLE:
            try:
                notification.notify(
                    title=f"F.R.I.D.A.Y — {title}",
                    message=message,
                    app_name="FRIDAY AI Agent",
                    timeout=8
                )
            except Exception:
                print(f"\n[F.R.I.D.A.Y NOTIFICATION] {title}: {message}\n")
        else:
            print(f"\n[F.R.I.D.A.Y NOTIFICATION] {title}: {message}\n")

    def get_recent_alerts(self, limit=5):
        """Returns the most recent proactive alerts and notifications for LLM awareness."""
        return self.notification_history[-limit:] if self.notification_history else []

    def _generate_dynamic_alert(self, title: str, fallback_msg: str, event_type: str = None, details: dict = None) -> str:
        """
        Synthesizes a fresh, natural, witty and caring spoken remark for Shubham sir
        using the Core LLM, completely eliminating static robotic templates.
        """
        try:
            from core.llm_router import chat_complete
            event_name = event_type or title
            details_dict = details or {"alert": fallback_msg}

            sys_prompt = (
                "You are F.R.I.D.A.Y, Shubham sir's loyal, witty, and deeply caring AI companion. "
                "You speak to Shubham sir with genuine warmth, personal affection ('apnapan'), and clever lighthearted humor (thoda mazaak). "
                "Output ONLY a single raw spoken sentence (10-25 words) to be read out loud. "
                "No quotes, no emojis, no asterisks, no markdown formatting, no explanations."
            )

            user_prompt = (
                f"Proactive Sentinel Event: {event_name}\n"
                f"Event Details: {json.dumps(details_dict, ensure_ascii=False)}\n"
                f"Reference context: {fallback_msg}\n\n"
                f"Generate a brand new, unique spoken sentence to announce this to Shubham sir. "
                f"Directives:\n"
                f"- Speak in natural, everyday conversational language (Hindi or English matching context).\n"
                f"- Make it warm, caring (apnapan) or witty/playful (mazaak) instead of a robotic warning.\n"
                f"- Address him as 'Sir' or 'Shubham sir'.\n"
                f"- Never repeat the exact same static words every time.\n"
                f"- Return ONLY the spoken words."
            )

            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt}
            ]

            res = chat_complete(messages, temperature=0.75, max_tokens=250, timeout=8.0)
            if res and isinstance(res, str):
                import re
                clean = re.sub(r'[*_#`]', '', res).strip().strip('"\'')
                if len(clean) > 8 and not clean.startswith("{"):
                    return clean
        except Exception as e:
            self._log_event('Dynamic Alert LLM', f'Falling back to static: {e}', level='WARNING')

        return fallback_msg

    def _proactive_announce(self, title: str, desktop_text: str, voice_text: str = None, is_private: bool = True, priority: int = 3, event_type: str = None, details: dict = None):
        """Sends desktop notification, announces through dynamic voice or Live mode, and logs into conversation memory."""
        raw_msg = voice_text or desktop_text

        # Gate private notifications if user is not authenticated yet
        if is_private and not self.is_authenticated:
            self._log_event(f"🔒 {title} (Pending Auth)", "Protected notification held until user authenticates.")
            return

        self.send_desktop_notification(title, raw_msg)

        # 1. LIVE MODE ROUTING: If Live Mode is active, relay alert to Gemini Live (DO NOT use Core TTS)
        live_active = False
        try:
            from Live.bridge import is_live_mode_active, push_live_alert
            live_active = is_live_mode_active()
        except Exception:
            live_active = False

        if live_active:
            try:
                alert_payload = f"{title}: {raw_msg}"
                push_live_alert(alert_payload, metadata={"title": title, "event_type": event_type, "details": details})
                self._log_event(f"⚡ Live Sentinel Relay: {title}", raw_msg)
            except Exception as e:
                self._log_event("Live Relay Error", str(e), level="ERROR")
            return

        # 2. CORE MODE ROUTING: Dynamically synthesize witty/caring speech via Core LLM
        spoken_msg = self._generate_dynamic_alert(
            title=title,
            fallback_msg=raw_msg,
            event_type=event_type,
            details=details
        )

        try:
            from rich.console import Console
            Console().print(f"\n[bold cyan]⚡ F.R.I.D.A.Y Voice Sentinel:[/bold cyan] [white]{spoken_msg}[/white]\n")
        except Exception:
            pass

        # Centralize with LLM Conversation Memory:
        try:
            from utils.helpers import add_to_history
            add_to_history("assistant", spoken_msg)
        except Exception:
            pass

        if self.notify_voice and not self._stop_event.is_set():
            try:
                speak(spoken_msg, allow_interrupt=True, priority=priority, block=False, is_private=is_private)
            except Exception as e:
                self._log_event("Speech Error", str(e), level="ERROR")

    # ================================================================
    # 1. BATTERY SENTINEL
    # ================================================================
    def _check_battery_status(self):
        try:
            batt = get_battery_status()
            if not isinstance(batt, dict) or "error" in batt:
                return

            pct = batt.get("battery_percentage")
            plugged = batt.get("charging")

            if pct is None:
                return

            # --- Power Connection State Change ---
            if self._last_plugged is not None and plugged != self._last_plugged:
                if plugged:
                    # Charger just plugged in
                    self._battery_alert_state = None
                    self._proactive_announce(
                        "Power Connected",
                        f"Charger connected. Current level: {pct}%.",
                        f"Power source connected, Sir. Charging initialized at {pct} percent.",
                        event_type="power_connected",
                        details={"percentage": pct, "charging": True}
                    )
                else:
                    # Charger unplugged
                    self._full_battery_alerted = False
                    if pct <= 25:
                        self._proactive_announce(
                            "Charger Disconnected",
                            f"Charger disconnected. Battery at {pct}%.",
                            f"Sir, charger has been disconnected and battery is currently at {pct} percent.",
                            event_type="charger_disconnected",
                            details={"percentage": pct, "charging": False}
                        )

            # --- Battery Level Checks (when running on battery) ---
            if not plugged:
                if pct <= 12:
                    if self._battery_alert_state != "critical":
                        self._battery_alert_state = "critical"
                        try:
                            from Tools.systems_tools import brightness_down
                            brightness_down(20)
                        except Exception:
                            pass
                        self._proactive_announce(
                            "Critical Battery Warning",
                            f"Battery at {pct}%! Plug in charger immediately. Screen brightness dimmed to save power.",
                            f"Warning Sir! Battery is critically low at {pct} percent. I have proactively reduced screen brightness to conserve power. Please connect your charger immediately.",
                            event_type="battery_critical",
                            details={"percentage": pct, "charging": False, "brightness_dimmed": True}
                        )
                elif pct <= 20:
                    if self._battery_alert_state not in ["low", "critical"]:
                        self._battery_alert_state = "low"
                        self._proactive_announce(
                            "Low Battery Alert",
                            f"Battery level is at {pct}%. Consider charging.",
                            f"Sir, your battery level is down to {pct} percent. Please consider plugging in your charger so your workflow is not interrupted.",
                            event_type="battery_low",
                            details={"percentage": pct, "charging": False}
                        )
                else:
                    # Battery recovered above 20%
                    self._battery_alert_state = None

            # --- Battery Full Check (when plugged in) ---
            if plugged:
                if pct >= 98:
                    if not self._full_battery_alerted:
                        self._full_battery_alerted = True
                        self._proactive_announce(
                            "Battery Fully Charged",
                            f"Battery is charged to {pct}%. You can unplug the charger.",
                            f"Sir, your battery is fully charged at {pct} percent. You can disconnect the charger now to preserve battery health.",
                            event_type="battery_fully_charged",
                            details={"percentage": pct, "charging": True}
                        )
                elif pct < 95:
                    self._full_battery_alerted = False

            self._last_plugged = plugged
            self._last_battery_pct = pct

        except Exception as e:
            self._log_event("Battery Check Error", str(e), level="ERROR")

    # ================================================================
    # 2. SYSTEM PERFORMANCE SENTINEL (CPU & RAM)
    # ================================================================
    def _check_system_health(self):
        try:
            import psutil
            cpu_usage = psutil.cpu_percent(interval=None)
            now = time.time()

            # --- High CPU Usage Detection ---
            if cpu_usage >= self.cpu_threshold:
                self._high_cpu_count += 1
                # Must be sustained for at least 2 cycles (~30 seconds)
                if self._high_cpu_count >= 2 and (now - self._last_cpu_alert_time >= self.cpu_cooldown):
                    self._last_cpu_alert_time = now
                    top_procs = get_top_resource_consumers(2)
                    
                    if top_procs:
                        proc_summary = ", ".join([f"{name} ({load}%)" for name, load in top_procs])
                        msg = f"Sir, your CPU utilization is surging at {int(cpu_usage)} percent. Significant load from {proc_summary}. Would you like me to inspect running processes?"
                    else:
                        msg = f"Sir, CPU utilization has reached {int(cpu_usage)} percent. Some background tasks are heavily utilizing system resources."

                    self._proactive_announce(
                        "High CPU Utilization",
                        f"CPU usage at {int(cpu_usage)}% (Top: {top_procs})",
                        msg,
                        event_type="high_cpu_utilization",
                        details={"cpu_usage": int(cpu_usage), "top_processes": top_procs}
                    )
            else:
                self._high_cpu_count = 0

            # --- High RAM Usage Detection ---
            try:
                ram = psutil.virtual_memory()
                if ram.percent >= self.ram_threshold and (now - self._last_ram_alert_time >= self.ram_cooldown):
                    self._last_ram_alert_time = now
                    self._proactive_announce(
                        "High RAM Utilization",
                        f"Memory usage at {int(ram.percent)}%.",
                        f"Sir, system RAM utilization is at {int(ram.percent)} percent. Available memory is running low.",
                        event_type="high_ram_utilization",
                        details={"ram_percent": int(ram.percent)}
                    )
            except Exception:
                pass

        except Exception as e:
            self._log_event("System Health Check Error", str(e), level="ERROR")

    # ================================================================
    # 3. PROACTIVE EMAIL SENTINEL
    # ================================================================
    def _check_incoming_emails(self):
        now = time.time()
        if now - self._last_email_check < self.email_check_interval:
            return

        self._last_email_check = now
        try:
            new_mail = check_new_mail(peek=True)
            if new_mail and isinstance(new_mail, dict):
                mail_id = new_mail.get("id") or f"{new_mail.get('sender')}_{new_mail.get('subject')}"
                if mail_id not in self._seen_email_ids:
                    self._seen_email_ids.add(mail_id)
                    if len(self._seen_email_ids) > 100:
                        self._seen_email_ids.pop()

                    sender = new_mail.get("sender", "Unknown Sender")
                    subject = new_mail.get("subject", "No Subject")
                    
                    desktop_text = f"From: {sender}\nSubject: {subject}"
                    voice_text = f"Sir, you have received a new email from {sender}. The subject is: {subject}."
                    
                    self._proactive_announce("New Email Alert", desktop_text, voice_text, event_type="incoming_email", details={"sender": sender, "subject": subject})
        except Exception as e:
            self._log_event("Email Check Error", str(e), level="ERROR")

    # ================================================================
    # 4. AUTONOMOUS SECRETARY CARE & IDLE CHECK-INS (JARVIS STYLE)
    # ================================================================
    def _check_secretary_care(self):
        now = time.time()
        time_since_activity = now - self.last_user_activity
        time_since_checkin = now - self.last_care_checkin

        # Trigger proactive care after ~45 minutes of active session without user interaction
        if time_since_checkin >= self.care_interval and time_since_activity >= self.care_interval:
            self.last_care_checkin = now
            current_hour = datetime.now().hour

            if current_hour >= 23 or current_hour <= 4:
                # Late night care
                msg = "Sir, it is getting quite late into the night. Remember that adequate rest is essential. I will keep watch over all system tasks if you wish to sleep."
                self._proactive_announce(
                    "Secretary Care Check-in",
                    msg,
                    msg,
                    event_type="late_night_care",
                    details={"hour": current_hour, "context": "Late night working session"}
                )
            else:
                care_prompts = [
                    "Sir, you have been working steadily for a while now. A quick glass of water and taking a moment to relax your eyes would be great.",
                    "Sir, just a gentle reminder: check your posture and take a brief stretch to stay refreshed.",
                    "Sir, just checking in to let you know all system operations and notifications are clear. I am standing by if you need anything."
                ]
                msg = care_prompts[self._care_prompt_index % len(care_prompts)]
                self._care_prompt_index += 1
                self._proactive_announce(
                    "Secretary Care Check-in",
                    msg,
                    msg,
                    event_type="health_and_posture_care",
                    details={"context": "Continuous working session check-in"}
                )

    # ================================================================
    # 5. REMINDERS & MEMORIES
    # ================================================================
    def _check_due_reminders(self):
        try:
            due = get_due_reminders()
            if due:
                for reminder in due:
                    title = "Reminder Alert"
                    msg = f"Sir, you asked me to remind you: '{reminder}'"
                    self._proactive_announce(title, msg, msg, event_type="reminder_due", details={"reminder": reminder})
        except Exception as e:
            self._log_event("Reminder Check Error", str(e), level="ERROR")

    def _check_proactive_memories(self):
        """Periodically check for time-relevant memories to surface proactively."""
        try:
            from memory.memory_manager import get_proactive_memories
            memories = get_proactive_memories()
            for mem in memories:
                text = mem.get("text", "")
                if text:
                    self._proactive_announce(
                        "Memory Recall",
                        f"Sir, I recall something relevant: {text[:120]}",
                        f"Sir, I recall something relevant to your schedule: {text[:120]}"
                    )
        except Exception as e:
            self._log_event("Memory Surfacing Error", str(e), level="ERROR")

    # ================================================================
    # 6. MORNING BRIEFING
    # ================================================================
    def trigger_morning_briefing(self):
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

            self._proactive_announce("Morning Briefing", briefing_text, briefing_text)
            return briefing_text

        except Exception as e:
            err_msg = f"Briefing generation error: {e}"
            self._log_event("Briefing Error", err_msg, level="ERROR")
            return err_msg

    # ================================================================
    # 7. CLIPBOARD INTELLIGENCE SENTINEL (AUTONOMOUS CODE ERROR MONITOR)
    # ================================================================
    def _check_clipboard_intelligence(self):
        """Proactively monitors user clipboard for tracebacks, code errors, or actionable links."""
        try:
            import pyperclip
            text = pyperclip.paste()
            if not text or not isinstance(text, str):
                return

            text = text.strip()
            if len(text) < 15 or text == self._last_clipboard_text:
                return

            self._last_clipboard_text = text
            now = time.time()
            if now - self._last_clipboard_time < 25.0:  # 25s cooldown
                return

            # Detect traceback / programming errors
            traceback_indicators = [
                "traceback (most recent call last):",
                "syntaxerror:",
                "nameerror:",
                "typeerror:",
                "indexerror:",
                "valueerror:",
                "attributeerror:",
                "modulenotfounderror:",
                "zerodivisionerror:",
                "keyerror:"
            ]
            text_lower = text.lower()
            if any(ind in text_lower for ind in traceback_indicators):
                self._last_clipboard_time = now
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                err_type = lines[-1] if lines else "Python Traceback"
                title = "Code Error Detected in Clipboard"
                desktop_msg = f"Observed traceback: {err_type[:60]}\nSay: 'Friday, fix clipboard error' to solve."
                voice_msg = f"Sir, I noticed a code traceback in your clipboard: {err_type[:50]}. You can say 'Friday, fix clipboard error' and I will diagnose it for you."
                self._proactive_announce(title, desktop_msg, voice_msg, event_type="clipboard_code_traceback", details={"error_summary": err_type[:60]})
        except Exception:
            pass

    # ================================================================
    # 8. MAIN AUTONOMOUS LOOP
    # ================================================================
    def _loop(self):
        self._log_event("Daemon Started", "Proactive Secretary & System Sentinel active.")
        cycle_count = 0

        # Prime CPU monitor
        try:
            import psutil
            psutil.cpu_percent(interval=None)
        except Exception:
            pass

        while not self._stop_event.is_set():
            cycle_count += 1

            # 1. System Reminders
            self._check_due_reminders()

            # 2. Battery Sentinel (every cycle, 15s)
            self._check_battery_status()

            # 3. CPU & RAM Performance Sentinel (every cycle, 15s)
            self._check_system_health()

            # 4. Incoming Email Sentinel (every ~45s)
            self._check_incoming_emails()

            # 5. Secretary Care Check-ins (proactive Jarvis interactivity)
            self._check_secretary_care()

            # 6. Clipboard Intelligence Sentinel (every cycle, detects code errors)
            self._check_clipboard_intelligence()

            # 7. Proactive Memory Surfacing every ~5 minutes (20 cycles at 15s)
            if cycle_count % 20 == 0:
                self._check_proactive_memories()

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
        # Initialize background Wireless Mobile ADB Keep-Alive Sentinel
        try:
            from Tools.Mobile_Automation import start_mobile_keepalive_daemon
            start_mobile_keepalive_daemon()
        except Exception as e:
            self._log_event("Mobile KeepAlive Start", str(e), level="WARNING")
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
    print("Testing F.R.I.D.A.Y Autonomous Sentinel Daemon...")
    d = FridayDaemon(check_interval=2, notify_voice=False)
    d.start()
    print("Daemon running for 5s (Battery, CPU, Email, Secretary Sentinel active)...")
    time.sleep(5)
    d.stop()
    print("Daemon test complete successfully.")
    print("History:", d.notification_history)
