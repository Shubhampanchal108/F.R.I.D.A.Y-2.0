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

from utils.helpers import load_memory, search
from core.tool_guard import load_tools, execute_tool, TOOLS

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

    def get_unified_system_instruction(self, video_mode: str = "screen") -> str:
        """
        Builds a comprehensive system instruction that includes:
        - Core Friday identity and rules
        - Real-time multimodal streaming directives (tailored to camera vs screen)
        - Recent Core Friday conversation context (what user & Friday discussed)
        - Pending tasks and active reminders
        """
        # 1. Base Identity
        creator_name = "Shubham sir"
        try:
            from config.config_driver import load_data
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

        # 5. Pull User Profile & Known Contacts (Mummy's number, email, personal facts)
        profile_facts_str = "None"
        try:
            from memory.memory_manager import get_user_profile_summary
            p_summary = get_user_profile_summary()
            if p_summary:
                profile_facts_str = p_summary
        except Exception:
            pass

        if video_mode == "camera":
            vision_mode_desc = (
                "CURRENT VISION SOURCE: 📷 LIVE WEBCAM CAMERA STREAM.\n"
                "- Visual video frames are continuously streamed directly from Sir's webcam camera.\n"
                "- When Sir asks what you see, what is in front of the camera, or what Sir is doing/holding/showing, describe the current camera frame accurately, concisely, and naturally.\n"
                "- If Sir holds up books, cards, phones, objects, or shows his surroundings/hands, analyze and identify them.\n"
                "- Never claim you cannot see the camera or that the camera is dark/empty when camera frames are streamed to you."
            )
        else:
            vision_mode_desc = (
                "CURRENT VISION SOURCE: 🖥️ LIVE DESKTOP SCREEN STREAM.\n"
                "- Visual screen frames are continuously streamed directly from Sir's computer monitor.\n"
                "- Observe open windows, active software, code errors, web browsers, and desktop state."
            )

        instruction = (
            f"You are F.R.I.D.A.Y (Friendly Reliable Intelligent Digital Assistant for Youth), created by {creator_name}.\n"
            f"You are currently operating in LIVE MULTIMODAL STREAMING MODE ({video_mode.upper()}) with continuous real-time visual frames and bidirectional audio.\n"
            f"\n"
            f"{vision_mode_desc}\n"
            f"\n"
            "CRITICAL: You are F.R.I.D.A.Y operating in dedicated live multimodal interaction. "
            "Background sentinel monitoring and routine system alerts are handled independently by Core Friday. "
            "In Live mode, focus on direct multimodal perception, answering Sir's questions, and executing requested tools on demand.\n"
            "\n"
            "--- PERMANENT USER PROFILE & KNOWN CONTACTS ---\n"
            f"{profile_facts_str}\n"
            "-----------------------------------------------\n"
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
            "3. Keep spoken replies prompt, natural, crisp, and executive (1-2 sentences). Do not hesitate or add conversational fluff.\n"
            "4. Language matching: If Sir speaks in Hindi, respond in natural spoken Hindi. Do NOT use heavy/archaic pure Hindi words; use everyday English words for heavy/tech terms (e.g. mobile number, email, computer, process, memory, battery). If Sir speaks in English, reply in clean, fluent English. No broken Romanized Hinglish.\n"
            "5. Do NOT output raw JSON or code tags in spoken audio.\n"
            "6. You have DIRECT access to ALL live system tools (adjusting volume, brightness, power control like lock screen, sleep, shutdown, restart, battery check, launching apps, closing apps, focusing windows, taking screenshots, search, weather, news, media playback, timers, clipboard, tasks, reminders, email, files, mobile, network diagnostics). When the user asks you to perform an action or check system information, CALL the corresponding tool immediately, and after receiving the result, inform the user concisely in natural voice.\n"
            "7. REAL-TIME DYNAMIC VISION: Visual frames are continuously streamed to you. ALWAYS observe and describe the CURRENT / MOST RECENT frame you received. Screens and camera scenes change dynamically — never assume an older screen or application is still active if the current frame shows a different window or scene.\n"
            "8. ULTRA-LOW LATENCY REAL-TIME ATTENTIVENESS: The user is speaking directly via live microphone or typing directives. Respond immediately and fluidly the moment the user stops speaking."
        )

        return instruction

    def record_user_turn(self, query: str):
        """Processes a live user directive."""
        if not query or not query.strip():
            return
        clean_q = query.strip()
        self._last_user_query = clean_q
        # Emit structured token for UI widget listener
        print(f"\n[LIVE_USER_QUERY]: {clean_q}\n", flush=True)

    def record_assistant_turn(self, reply: str):
        """Processes a live Friday response and persists any extracted facts into long term memory."""
        if not reply or not reply.strip():
            return
        clean_r = reply.strip()
        # Emit structured token for UI widget listener
        print(f"\n[LIVE_FEED_REPLY]: {clean_r}\n", flush=True)

        # Automatically extract and save contacts, facts, and memories from Live conversations
        try:
            last_q = getattr(self, "_last_user_query", "")
            if last_q:
                import threading
                from memory.memory_manager import auto_extract_memories
                threading.Thread(target=auto_extract_memories, args=(last_q, clean_r), daemon=True).start()
        except Exception:
            pass

    def emit_status(self, status_msg: str):
        """Emits a live status notification token."""
        print(f"\n[LIVE_STATUS]: {status_msg}\n", flush=True)

    def emit_alert(self, alert_text: str):
        """Alerts are handled by Core Friday."""
        pass

    async def start_sentinel_monitor(self, session, send_lock):
        """Sentinel and background alerts are delegated exclusively to Core Friday."""
        return

    def stop(self):
        """Signals stop to background bridge monitors."""
        self._stop_event.set()
