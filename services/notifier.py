import threading
import time
from datetime import datetime
import os
import sys
import json
import re

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from voice.speak import speak

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


class NotificationEngine:
    """
    Centralized notification & spoken alert engine for F.R.I.D.A.Y.
    Handles:
    - Desktop notifications (Plyer/Toast)
    - Live Mode routing (Gemini Multimodal Live relay)
    - LLM dynamic voice remark synthesis (warmth, apnapan, wit)
    - Event history logging
    """

    def __init__(self, notify_voice=True, on_event_callback=None):
        self.notify_voice = notify_voice
        self.on_event_callback = on_event_callback
        self.notification_history = []
        self.is_authenticated = False

    def log_event(self, title: str, message: str, level: str = "INFO"):
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
        self.log_event(title, message)
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

    def generate_dynamic_alert(self, title: str, fallback_msg: str, event_type: str = None, details: dict = None) -> str:
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
                clean = re.sub(r'[*_#`]', '', res).strip().strip('"\'')
                if len(clean) > 8 and not clean.startswith("{"):
                    return clean
        except Exception as e:
            self.log_event('Dynamic Alert LLM', f'Falling back to static: {e}', level='WARNING')

        return fallback_msg

    def announce(
        self,
        title: str,
        desktop_text: str,
        voice_text: str = None,
        is_private: bool = False,
        priority: int = 3,
        event_type: str = None,
        details: dict = None,
        stop_event: threading.Event = None
    ):
        """Sends desktop notification, announces through dynamic voice or Live mode, and logs into conversation memory."""
        raw_msg = voice_text or desktop_text

        # Gate private notifications if user is not authenticated yet
        if is_private and not self.is_authenticated:
            self.log_event(f"🔒 {title} (Pending Auth)", "Protected notification held until user authenticates.")
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
                self.log_event(f"⚡ Live Sentinel Relay: {title}", raw_msg)
            except Exception as e:
                self.log_event("Live Relay Error", str(e), level="ERROR")
            return

        # 2. CORE MODE ROUTING: Dynamically synthesize witty/caring speech via Core LLM
        spoken_msg = self.generate_dynamic_alert(
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

        if self.notify_voice and (stop_event is None or not stop_event.is_set()):
            try:
                speak(spoken_msg, allow_interrupt=True, priority=priority, block=False, is_private=is_private)
            except Exception as e:
                self.log_event("Speech Error", str(e), level="ERROR")

