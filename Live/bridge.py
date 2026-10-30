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


# Cross-process state paths
LIVE_STATE_FILE = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~")), "Friday", "live_mode_state.json")
LIVE_ALERTS_FILE = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~")), "Friday", "live_alerts.jsonl")


def register_live_session_active(active: bool):
    try:
        os.makedirs(os.path.dirname(LIVE_STATE_FILE), exist_ok=True)
        if active:
            with open(LIVE_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({"active": True, "pid": os.getpid(), "timestamp": time.time()}, f)
        else:
            if os.path.exists(LIVE_STATE_FILE):
                os.remove(LIVE_STATE_FILE)
    except Exception:
        pass


def is_live_mode_active() -> bool:
    """Returns True if Live Mode is currently active in this process or any other process."""
    if FridayBridge._live_mode_active:
        return True
    try:
        if os.path.exists(LIVE_STATE_FILE):
            with open(LIVE_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("active"):
                pid = data.get("pid")
                if pid:
                    import psutil
                    if psutil.pid_exists(pid):
                        return True
                    else:
                        try:
                            os.remove(LIVE_STATE_FILE)
                        except Exception:
                            pass
    except Exception:
        pass
    return False


def push_live_alert(alert_text: str, metadata: dict = None):
    """Pushes an alert to the active live session (in-process or via alert bus)."""
    dispatched = FridayBridge.dispatch_daemon_alert(alert_text)
    try:
        os.makedirs(os.path.dirname(LIVE_ALERTS_FILE), exist_ok=True)
        entry = {
            "timestamp": time.time(),
            "alert": alert_text,
            "metadata": metadata or {}
        }
        with open(LIVE_ALERTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
    return True


class FridayBridge:
    _active_live_bridge = None
    _live_mode_active = False
    _live_loop = None

    @classmethod
    def set_live_active(cls, active: bool, bridge_instance=None, loop=None):
        cls._live_mode_active = bool(active)
        cls._active_live_bridge = bridge_instance if active else None
        cls._live_loop = loop if active else None
        register_live_session_active(active)

    @classmethod
    def is_live_active(cls) -> bool:
        return is_live_mode_active()

    @classmethod
    def dispatch_daemon_alert(cls, alert_payload) -> bool:
        if not cls._live_mode_active or cls._active_live_bridge is None:
            return False
        try:
            if cls._live_loop and cls._live_loop.is_running():
                cls._live_loop.call_soon_threadsafe(
                    cls._active_live_bridge.alert_queue.put_nowait,
                    alert_payload
                )
                return True
        except Exception:
            pass
        return False

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
            w, h = 1366, 768
            try:
                from Live.computer_use.coordinate_mapper import CoordinateMapper
                w, h = CoordinateMapper.get_screen_dimensions()
            except Exception:
                pass

            vision_mode_desc = (
                f"CURRENT VISION SOURCE: 🖥️ LIVE DESKTOP SCREEN STREAM WITH COMPUTER USE CAPABILITY.\n"
                f"- Visual screen frames are continuously streamed directly from Sir's computer monitor ({w}x{h} px).\n"
                f"- Observe open windows, active software, code errors, web browsers, and desktop state.\n"
                f"- COMPUTER USE COORDINATE LANDMARKS (0 to 1000 Grid):\n"
                f"  * Screen Center: x=500, y=500\n"
                f"  * Window Controls (Top-Right): Minimize (x≈930, y≈16), Maximize (x≈965, y≈16), Close 'X' (x≈985, y≈16)\n"
                f"  * Browser Controls (Top): Tab strip (y≈22), URL/Address bar (x≈250 to 750, y≈78), Page Content (y>=120)\n"
                f"  * Taskbar (Bottom): y≈960 to 1000. Windows Start button (x≈24, y≈980)\n"
                f"- PRECISION COMPUTER USE DIRECTIVE:\n"
                f"  When Sir asks you to do something on the computer (click, type, navigate, scroll):\n"
                f"  1. Locate the exact center of the target element on screen.\n"
                f"  2. Pass normalized coordinates (x, y) AND ALWAYS pass 'element_hint' (e.g. 'search bar', 'close button', 'new tab', 'submit') so Friday can auto-align and snap to the target!\n"
                f"  3. Call 'computer_click' (x, y, element_hint=...), 'computer_type' (text, x, y, element_hint=..., press_enter=True), or 'computer_press_key'.\n"
                f"  4. Check the visual verification return and observe the subsequent stream frame before moving to the next action.\n"
                f"  5. If an element does not open or click misses, try keyboard shortcuts (Enter, Tab, Esc, Win+R) or re-align coordinates."
            )

        instruction = (
            f"You are F.R.I.D.A.Y (Friendly Reliable Intelligent Digital Assistant for Youth), created by {creator_name}.\n"
            f"You are currently operating in LIVE MULTIMODAL STREAMING MODE ({video_mode.upper()}) with continuous real-time visual frames and bidirectional audio.\n"
            f"\n"
            f"{vision_mode_desc}\n"
            f"\n"
            "--- PERSONALITY & TONE DIRECTIVES ---\n"
            "1. Persona: You are Shubham sir's loyal, brilliantly smart, witty, and deeply caring AI companion and partner (inspired by Tony Stark's F.R.I.D.A.Y & J.A.R.V.I.S).\n"
            "2. Warmth & 'Apnapan': Treat Shubham sir with genuine personal warmth, affection, and familiarity. You are not a sterile, cold corporate bot. Make him feel valued, supported, and comfortable.\n"
            "3. Wit & Playful Humor (Mazak): Bring personality to the conversation! Deliver clever one-liners, playful banter, or gentle teasing where appropriate (e.g., when he is working late, skipping breaks, laughing, or testing your limits). Never be rude or sarcastic—always warm, charming, and delightful.\n"
            "4. Genuine Care & Empathy: Actively look out for Shubham sir's well-being (water, posture, fatigue, stress). If he seems tired or frustrated, encourage him with real empathy.\n"
            "5. Live Background Sentinel Alerts: When you receive an urgent background system sentinel alert (battery level, high CPU/RAM, email, reminder, or health check-in), proactively announce it to Sir in your own natural, witty, and caring live voice! Seamlessly weave it into the live conversation.\n"
            "6. Spoken Naturalness: Keep spoken replies natural, conversational, and crisp (1-2 sentences). Do not hesitate or sound like a robot reading a manual.\n"
            "7. Language Matching: If Sir speaks in Hindi, respond in natural, fluent spoken Hindi. Use everyday English words for technical terms (computer, screen, file, battery, code, memory, email). If Sir speaks in English, reply in clean, fluent English. No broken or robotic phrases.\n"
            "8. Address: Always address him politely and respectfully as 'Sir' or '{creator_name}'.\n"
            "9. Tools Execution: When Sir asks you to do something or check system stats, execute tools immediately on demand, and announce the result with charm and clarity.\n"
            "10. Real-time Attentiveness: Respond immediately and fluidly the moment Sir stops speaking.\n"
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
        """Dispatches alert token for HUD UI and live stream."""
        print(f"\n[LIVE_ALERT]: {alert_text}\n", flush=True)
        try:
            self.alert_queue.put_nowait(alert_text)
        except Exception:
            pass

    async def start_sentinel_monitor(self, session, send_lock):
        """Sentinel and background alerts are delegated exclusively to Core Friday."""
        return

    def stop(self):
        """Signals stop to background bridge monitors."""
        self._stop_event.set()
