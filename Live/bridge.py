"""
=============================================================================
F.R.I.D.A.Y LIVE MULTIMODAL // COGNITIVE SYNCHRONIZATION BRIDGE
=============================================================================
Connects Live Multimodal Friday directly with Core Friday:
1. Shared Context: Pulls recent conversation history, tasks & reminders.
2. Shared Memory: Synchronizes all live interactions back into Core memory.
3. Sentinel Alert Relay: Intercepts daemon alerts (low battery, reminders, emails)
   and injects them as urgent turns so Live Friday announces them in real-time.
4. IPC & UI Dispatcher: Emits structured tokens for the desktop HUD widget.
=============================================================================
"""

import os
import sys
import time
import json
import asyncio
from datetime import datetime

# UTF-8 stdout reconfigure for Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Parent directory for relative imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utiles import load_memory, add_to_history, search
from Tool_guard import load_tools, execute_tool, TOOLS
from daemon import daemon_instance

# Pre-load tools registry on import
load_tools()


class FridayBridge:
    """
    Bidirectional synchronization conduit between Core Friday and Live Friday.
    """

    def __init__(self):
        self.input_queue = asyncio.Queue()
        self.alert_queue = asyncio.Queue()
        self._last_alert_timestamp = time.time()
        self._daemon_listener_task = None
        self._stop_event = asyncio.Event()

    def get_unified_system_instruction(self) -> str:
        """
        Builds a comprehensive system instruction that includes:
        - Core Friday identity and rules
        - Real-time multimodal streaming directives
        - Recent Core Friday conversation context (what user & Friday discussed)
        - Pending tasks and active reminders
        """
        # 1. Base Identity
        creator_name = "Shubham sir"
        try:
            from config_driver import load_data
            data = load_data()
            u_name = data.get("USER", {}).get("Name", "Shubham")
            creator_name = f"{u_name} sir"
        except Exception:
            pass

        # 2. Pull Recent Core Memory Context
        recent_context_lines = []
        try:
            mem = load_memory()
            conv = mem.get("conversation_history", [])
            recent_turns = conv[-8:] if conv else []
            for t in recent_turns:
                role = "User" if t.get("role") in ["user", "human"] else "Friday"
                c = t.get("content", "")
                if c and not c.startswith("{") and len(c) < 300:
                    recent_context_lines.append(f"  [{role}]: {c.strip()}")
        except Exception:
            pass
        context_str = "\n".join(recent_context_lines) if recent_context_lines else "  (No prior conversation recorded)"

        # 3. Pull Pending Tasks
        task_str = "None"
        try:
            from Tools.Todo import list_tasks
            tasks = list_tasks()
            if isinstance(tasks, list) and tasks:
                task_str = ", ".join([str(t) for t in tasks[:5]])
        except Exception:
            pass

        # 4. Pull Active Reminders
        rem_str = "None"
        try:
            from Tools.reminder import list_reminders
            r_data = list_reminders()
            if isinstance(r_data, dict):
                rems = r_data.get("reminders", [])
                active_rems = [r.get("text", "") for r in rems if not r.get("done") and r.get("enabled", True)]
                if active_rems:
                    rem_str = ", ".join(active_rems[:5])
        except Exception:
            pass

        instruction = (
            f"You are F.R.I.D.A.Y (Friendly Reliable Intelligent Digital Assistant for Youth), created by {creator_name}.\n"
            "You are currently operating in LIVE MULTIMODAL STREAMING MODE with continuous real-time screen/camera frames and bidirectional audio.\n"
            "\n"
            "CRITICAL: YOU ARE NOT AN ISOLATED AGENT. You are the exact same F.R.I.D.A.Y that manages the user's desktop, tasks, reminders, and system sentinel. "
            "You have direct memory of what Core Friday was working on with Sir.\n"
            "\n"
            "--- RECENT CORE FRIDAY CONTEXT ---\n"
            f"Recent Conversation History with Sir:\n{context_str}\n"
            f"Active To-Do Tasks: {task_str}\n"
            f"Pending Reminders: {rem_str}\n"
            "-----------------------------------\n"
            "\n"
            "Rules & Directives:\n"
            f"1. Always address the user politely and respectfully as 'Sir' or '{creator_name}'.\n"
            "2. If asked about what is on screen or in front of the camera, describe it accurately, pointing out code, UI elements, errors, or objects.\n"
            "3. Keep spoken replies natural, conversational, concise, and executive (around 1-3 sentences unless explaining a complex technical topic).\n"
            "4. Support both English and natural Hindi (Hinglish) seamlessly based on the user's language.\n"
            "5. Do NOT output raw JSON or code tags in spoken audio.\n"
            "6. You have DIRECT access to ALL live system tools (adjusting volume, brightness, battery check, launching apps, closing apps, focusing windows, taking screenshots, search, weather, news, media playback, timers, clipboard, tasks, reminders, email, files, mobile, network diagnostics). When the user asks you to perform an action or check system information, CALL the corresponding tool immediately, and after receiving the result, inform the user concisely in natural voice.\n"
            "7. REAL-TIME DYNAMIC VISION: Visual frames are continuously streamed to you. ALWAYS observe and describe the CURRENT / MOST RECENT frame you received. Screens and camera scenes change dynamically — never assume an older screen or application is still active if the current frame shows a different window or scene.\n"
            "8. PROACTIVE SENTINEL ALERTS: If you receive a [SYSTEM NOTIFICATION / SENTINEL ALERT] turn, it is an urgent alert from Core Friday's background sentinel (e.g., low battery, due reminder, incoming email, health break). Immediately announce this alert to Sir politely and clearly in voice.\n"
            "9. REAL-TIME VOICE ATTENTIVENESS: The user is speaking directly to you via live microphone streaming. Always listen attentively to what the user says. The moment you hear the user speak or ask a question, answer immediately in natural voice."
        )

        return instruction

    def record_user_turn(self, query: str):
        """Records a user query in Core Friday conversation memory."""
        if not query or not query.strip():
            return
        clean_q = query.strip()
        try:
            add_to_history("user", clean_q)
        except Exception:
            pass
        # Emit structured token for UI widget listener
        print(f"\n[LIVE_USER_QUERY]: {clean_q}\n", flush=True)

    def record_assistant_turn(self, reply: str):
        """Records a Friday response in Core Friday conversation memory."""
        if not reply or not reply.strip():
            return
        clean_r = reply.strip()
        try:
            add_to_history("assistant", clean_r)
        except Exception:
            pass
        # Emit structured token for UI widget listener
        print(f"\n[LIVE_FEED_REPLY]: {clean_r}\n", flush=True)

    def emit_status(self, status_msg: str):
        """Emits a live status notification token."""
        print(f"\n[LIVE_STATUS]: {status_msg}\n", flush=True)

    def emit_alert(self, alert_text: str):
        """Emits a proactive alert token."""
        print(f"\n[LIVE_ALERT]: {alert_text}\n", flush=True)

    async def start_sentinel_monitor(self, session, send_lock):
        """
        Background sentinel monitor that checks Core Friday's daemon alerts
        and forwards them to Gemini Live so Friday speaks them out in real time.
        """
        last_notif_count = len(daemon_instance.notification_history)

        while not self._stop_event.is_set():
            await asyncio.sleep(2.0)
            if self._stop_event.is_set():
                break

            try:
                # 1. Check newly added alerts from daemon notification history
                current_history = daemon_instance.notification_history
                if len(current_history) > last_notif_count:
                    new_alerts = current_history[last_notif_count:]
                    last_notif_count = len(current_history)

                    for alert in new_alerts:
                        title = alert.get("title", "Sentinel Notice")
                        msg = alert.get("message", "")
                        alert_prompt = f"[SYSTEM NOTIFICATION / SENTINEL ALERT]: {title} — {msg}. Please inform Sir right now in voice."

                        self.emit_alert(f"{title}: {msg}")

                        try:
                            from google.genai import types
                            async with send_lock:
                                await session.send_client_content(
                                    turns=[types.Content(role="user", parts=[types.Part(text=alert_prompt)])],
                                    turn_complete=True
                                )
                        except Exception as e:
                            pass

                # 2. Check due reminders directly
                from Tools.reminder import get_due_reminders
                due_res = get_due_reminders()
                if isinstance(due_res, dict) and due_res.get("due_reminders"):
                    for rem in due_res["due_reminders"]:
                        rem_text = rem.get("text", "")
                        alert_prompt = f"[SYSTEM NOTIFICATION / SENTINEL ALERT]: Scheduled reminder '{rem_text}' is DUE NOW. Please alert Sir."
                        self.emit_alert(f"Reminder Due: {rem_text}")
                        try:
                            from google.genai import types
                            async with send_lock:
                                await session.send_client_content(
                                    turns=[types.Content(role="user", parts=[types.Part(text=alert_prompt)])],
                                    turn_complete=True
                                )
                        except Exception:
                            pass

            except Exception:
                await asyncio.sleep(2.0)

    def stop(self):
        """Signals stop to background bridge monitors."""
        self._stop_event.set()
