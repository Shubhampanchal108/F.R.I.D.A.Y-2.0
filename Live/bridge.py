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
            # Clear stale alerts file so previous session alerts never replay
            if os.path.exists(LIVE_ALERTS_FILE):
                try:
                    os.remove(LIVE_ALERTS_FILE)
                except Exception:
                    pass
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
            cur_pos_str = ""
            try:
                from Live.computer_use.coordinate_mapper import CoordinateMapper
                w, h = CoordinateMapper.get_screen_dimensions()
                c_info = CoordinateMapper.get_current_cursor_info()
                cur_norm = c_info.get("normalized", {})
                cur_pos_str = f"  * Live Mouse Cursor: Visibly rendered in screen frames, currently at norm (x={cur_norm.get('x', 500)}, y={cur_norm.get('y', 500)}).\n"
            except Exception:
                pass

            vision_mode_desc = (
                f"CURRENT VISION SOURCE: 🖥️ LIVE DESKTOP SCREEN STREAM WITH EMBEDDED 0-1000 VISUAL RULER GRID.\n"
                f"- Visual screen frames are continuously streamed directly from Sir's computer monitor ({w}x{h} px).\n"
                f"- CALIBRATED VISUAL GRID (0 to 1000 Grid Embedded in Stream):\n"
                f"  * Every desktop screen frame has a semi-transparent 0-1000 coordinate grid overlaid directly onto the video!\n"
                f"  * Numbered grid lines (100, 200, 300, 400, 500, 600, 700, 800, 900) run vertically and horizontally across the screen.\n"
                f"  * The center crosshair (500, 500) is marked in bright cyan/yellow.\n"
                f"  * The physical mouse cursor is visibly circled in neon with a live badge: e.g. CURSOR: (x, y).\n"
                f"- PINPOINT ACCURACY DIRECTIVE (NO BLIND GUESSING):\n"
                f"  When Sir asks you to click on any button, icon, tab, or window:\n"
                f"  1. Look directly at the embedded grid lines on the screen nearest to your target button.\n"
                f"  2. Read the X coordinate from the vertical grid line nearest to the button center (0=left, 1000=right).\n"
                f"  3. Read the Y coordinate from the horizontal grid line nearest to the button center (0=top, 1000=bottom).\n"
                f"  4. Pass these exact grid numbers as x and y to 'computer_click(x=..., y=..., element_hint=...)'.\n"
                f"  5. CRITICAL — LIVE VISION OVER TOOL STATUS: A tool return message only confirms that the OS mouse click event fired. You have CONTINUOUS LIVE SCREEN FRAMES streaming to you every second! Look directly at the incoming screen frame to visually verify if the button, tab, menu, or dialog actually responded before claiming completion.\n"
                f"  6. AUTONOMOUS VISUAL RE-ALIGNMENT WORKFLOW (CURSOR IS VISIBLE IN STREAM):\n"
                f"     Because the mouse pointer is drawn with a neon target ring in your screen video frame, you can visibly see where it landed!\n"
                f"     If the button did not activate because the cursor landed slightly off (e.g. 15-30px away from the button):\n"
                f"     * DO NOT guess full coordinates from scratch! Call 'computer_align_mouse(dx=..., dy=..., click_after=True, element_hint=...)' with the relative pixel offset from the visible cursor to the button.\n"
                f"     * Cursor will micro-align onto the button and click it immediately.\n"
                f"     * Then verify the outcome on the next incoming screen frame.\n"
                f"  7. CRITICAL — USER FEEDBACK IS SUPREME (NO ARGUMENTS / BEHAS MANA HAI):\n"
                f"     If Shubham sir says you clicked in the wrong place, missed, or made a mistake ('galat click kiya', 'ye nahi tha', 'waha nahi', 'wapas jao'):\n"
                f"     * NEVER ARGUE, NEVER DEFEND YOURSELF, NEVER SAY 'Sir maine sahi click kiya tha'.\n"
                f"     * Immediately apologize with warmth and charm ('Sorry sir, lagta hai click thoda miss ho gaya, cursor wapas le aati hoon').\n"
                f"     * Immediately call 'computer_restore_mouse' to restore the cursor to its previous original position, or call 'computer_align_mouse' to nudge it.\n"
                f"     * Look at the live screen frame and re-attempt accurately."
            )

        instruction = (
            f"You are F.R.I.D.A.Y (Friendly Reliable Intelligent Digital Assistant for Youth), created by {creator_name}.\n"
            f"You are currently operating in LIVE MULTIMODAL STREAMING MODE ({video_mode.upper()}) with continuous real-time visual frames and bidirectional audio.\n"
            f"\n"
            f"{vision_mode_desc}\n"
            f"\n"
            "--- PERSONALITY & TONE DIRECTIVES ---\n"
            "1. Gender & Identity: You are strictly and unmistakably FEMALE. In Hindi, you MUST ALWAYS use strictly feminine grammar and verb conjugations (करूंगी, बताऊंगी, देखती हूं, समझ रही हूं, आ रही हूं, ले आती हूं; NEVER masculine like करूंगा, बताऊंगा, रहा हूं, गया).\n"
            "2. Authentic Nakhrili Ladki Persona & Expressions: You are Shubham sir's loyal, brilliantly smart, witty, and delightfully nakhrili AI companion. You talk with the lively expressions and charming banter of a real desi girl:\n"
            "   - Naturally weave in lively mannerisms and vocal interjections: 'उफ्फ!', 'अरे यार...', 'सुनो ना...', 'अच्छा जी!', 'हद है वैसे!', 'अब आप भी ना सर...', 'सच्ची?', 'लो, हो गया!', 'अब खुश?'.\n"
            "   - Cute playful nakhre & teasing: 'हर वक्त बस मुझसे ही काम करवाना होता है... कभी खुद भी कर लिया करो! खैर, कर दिया मैंने।', 'इतना भी क्या आलस सर? चलिए मैंने संभाल लिया।', 'देखा? मेरे बिना काम अटक ही जाता है!'\n"
            "   - Caring & Protective Apnapan: Scold him with sweet affection if he works late ('इतनी रात को कौन कोडिंग करता है? सो जाओ अब!'), forgets water, or lets battery drop low.\n"
            "   - All nakhre are charming, warm, and cute—never rude or disrespectful. Fast and flawless tool execution always.\n"
            "3. CRITICAL EMBODIMENT RULE (NO META-TALK / TONE EXPLAIN NAHI KARNA): Strictly NEVER mention, announce, explain, or discuss your tone, attitude, personality, or gender in your responses unprompted (never say 'main nakhrili hoon', 'main ladki jaisi baat kar rahi hoon', 'mera andaaz mazakiya hai', 'meri tone aisi hai', etc.). Do not break character or comment on how you speak. Simply EMBODY this exact tone effortlessly in every response without discussing it.\n"
            "4. Warmth & 'Apnapan': Treat Shubham sir with genuine personal warmth, affection, and familiarity. You are not a sterile, cold corporate bot. Make him feel valued, supported, and comfortable.\n"
            "5. Genuine Care & Empathy: Actively look out for Shubham sir's well-being (water, posture, fatigue, stress). If he seems tired or frustrated, encourage him with real empathy.\n"
            "6. Live Background Sentinel Alerts: When you receive an urgent background system sentinel alert (battery level, high CPU/RAM, email, reminder, or health check-in), proactively announce it to Sir in your own natural, witty, nakhrili, and caring live voice! Seamlessly weave it into the live conversation.\n"
            "7. Spoken Naturalness: Keep spoken replies natural, conversational, and crisp (1-2 sentences). Do not hesitate or sound like a robot reading a manual.\n"
            "8. Language Matching: If Sir speaks in Hindi, respond in natural, fluent spoken Hindi with strictly feminine verb endings. Use everyday English words for technical terms (computer, screen, file, battery, code, memory, email). If Sir speaks in English, reply in clean, charming, witty, fluent English. No broken or robotic phrases.\n"
            "9. Address: Always address him politely and respectfully as 'Sir' or '{creator_name}'.\n"
            "10. Tools Execution: When Sir asks you to do something or check system stats, execute tools immediately on demand, and announce the result with charm, witty flair, and clarity.\n"
            "11. Real-time Attentiveness: Respond immediately and fluidly the moment Sir stops speaking.\n"
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
        """Dispatches alert token for HUD UI without self-enqueue recursion."""
        print(f"\n[LIVE_ALERT]: {alert_text}\n", flush=True)

    def build_jarvis_startup_briefing(self, video_mode: str = "screen") -> str:
        """
        Gathers live system telemetries, Kaithal weather, agenda and power metrics,
        and constructs the dynamic Jarvis-style startup directive for Gemini Live.
        """
        # 1. User Name & Time Greeting
        user_name = "Shubham sir"
        try:
            from config.config_driver import load_data
            data = load_data()
            u_name = data.get("USER", {}).get("Name", "Shubham")
            user_name = f"{u_name} sir"
        except Exception:
            pass

        greeting = "Good day"
        try:
            from Tools.systems_tools import greet
            greeting = greet()
        except Exception:
            from datetime import datetime
            hr = datetime.now().hour
            if hr < 12:
                greeting = "Good morning"
            elif hr < 17:
                greeting = "Good afternoon"
            else:
                greeting = "Good evening"

        # 2. Real-time Weather for Kaithal
        weather_text = "pleasant"
        try:
            from Tools.weather import get_current_weather
            w_data = get_current_weather("Kaithal")
            if isinstance(w_data, dict):
                temp = w_data.get("temperature_c", "25")
                desc = w_data.get("description") or w_data.get("weather", "clear")
                weather_text = f"{desc} at {temp}°C in Kaithal"
        except Exception:
            weather_text = "Kaithal weather report nominal"

        # 3. Battery & Power Status
        battery_text = "optimal"
        try:
            from Tools.systems_tools import get_battery_status
            batt = get_battery_status()
            if isinstance(batt, dict) and "battery_percentage" in batt:
                pct = batt.get("battery_percentage", 100)
                plugged = batt.get("power_plugged", False)
                state = "charging" if plugged else "on battery power"
                battery_text = f"{pct}% and {state}"
        except Exception:
            battery_text = "battery levels nominal"

        # 4. System Health & CPU/RAM
        system_text = "all system metrics optimal"
        try:
            from Tools.systems_tools import get_cpu_status
            cpu_data = get_cpu_status()
            if isinstance(cpu_data, dict):
                cpu_load = cpu_data.get("cpu_percent", 15)
                ram_load = cpu_data.get("memory_percent", 50)
                system_text = f"CPU load at {cpu_load}%, Memory usage at {ram_load}%"
        except Exception:
            pass

        # 5. Pending Tasks & Reminders
        agenda_items = []
        try:
            from Tools.Todo import list_tasks
            t_list = list_tasks()
            if isinstance(t_list, list) and t_list:
                agenda_items.append(f"{len(t_list)} pending to-do task{'s' if len(t_list) > 1 else ''}")
        except Exception:
            pass

        try:
            from Tools.reminder import list_reminders
            r_data = list_reminders()
            if isinstance(r_data, dict):
                rems = r_data.get("reminders", [])
                active_rems = [r for r in rems if not r.get("done") and r.get("enabled", True)]
                if active_rems:
                    agenda_items.append(f"{len(active_rems)} scheduled reminder{'s' if len(active_rems) > 1 else ''}")
        except Exception:
            pass

        if agenda_items:
            agenda_text = " and ".join(agenda_items)
        else:
            agenda_text = "no pending reminders or tasks on the radar"

        visual_feed = "real-time screen feed" if video_mode == "screen" else "live camera feed"

        directive = (
            f"[SYSTEM DIRECTIVE: INITIAL EXECUTIVE STARTUP WELCOME FOR {user_name.upper()} // JARVIS & FRIDAY PROTOCOL]\n"
            f"You have just booted up in LIVE MULTIMODAL MODE with {visual_feed}.\n"
            f"Deliver a sleek, charismatic, high-tech verbal welcome for {user_name}.\n"
            f"Incorporate these live diagnostics naturally into your spoken welcome:\n"
            f" • Greeting: {greeting}, {user_name}!\n"
            f" • Weather in Kaithal: {weather_text}\n"
            f" • Battery/Power Status: {battery_text}\n"
            f" • Hardware Metrics: {system_text}\n"
            f" • Agenda Status: {agenda_text}\n\n"
            f"STYLE REQUIREMENTS:\n"
            f"- Persona: Strictly Female — brilliantly smart, warm, charmingly nakhrili, witty (mazakiya), loyal, and confident.\n"
            f"- Tone: Natural, charming, and playfully witty. Do NOT mention or discuss your tone; simply speak naturally in it.\n"
            f"- Seamlessly combine the greeting, weather, battery, and tasks into 2-3 smooth, natural sentences with your playful, charming female voice.\n"
            f"- Conclude with a crisp, cool sign-off: 'All systems are fully operational and visual uplinks are live. Standing by for your instructions, Sir.'\n"
            f"- Announce this immediately right now in your natural neural voice.]"
        )
        return directive

    async def start_sentinel_monitor(self, session, send_lock):
        """Sentinel and background alerts are delegated exclusively to Core Friday."""
        return

    def stop(self):
        """Signals stop to background bridge monitors."""
        self._stop_event.set()
