"""
=============================================================================
F.R.I.D.A.Y 2.0 // AI CORNER WIDGET & HOLOGRAPHIC HUD
=============================================================================
A sleek, floating screen-corner AI assistant widget featuring:
- Siri & Iron Man Arc-Reactor inspired glowing neural orb
- Interactive HUD chat panel with Markdown & real-time tool execution status
- Voice Recognition (Microphone) & Instant Audio Response (Zero-Silence)
- Global Hotkey (Ctrl + Space) to summon or dismiss from anywhere on Windows
- Mini-Orb / Full-HUD collapsibility
=============================================================================
"""

import os
import sys
import time
import json
import threading
import ctypes
from ctypes import wintypes
import warnings
import logging

# ===========================================================================
# ENVIRONMENT & TELEMETRY SILENCING
# ===========================================================================
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_LOG_LEVEL"] = "ERROR"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.ERROR)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

import webview
import keyboard

# Global lazy references
_brain_func = None
_speak_func = None
_speech_recog_func = None
_instant_filler_func = None
_daemon = None

def get_brain():
    global _brain_func
    if _brain_func is None:
        from Brain import Brain
        _brain_func = Brain
    return _brain_func

def get_speak():
    global _speak_func
    if _speak_func is None:
        from speak import speak
        _speak_func = speak
    return _speak_func

def get_speech_recog():
    global _speech_recog_func
    if _speech_recog_func is None:
        from voice_input import SpeechRecognition
        _speech_recog_func = SpeechRecognition
    return _speech_recog_func

def get_instant_filler():
    global _instant_filler_func
    if _instant_filler_func is None:
        try:
            from instant_filler import trigger_instant_filler
            _instant_filler_func = trigger_instant_filler
        except Exception:
            _instant_filler_func = lambda q, audio_enabled=True: None
    return _instant_filler_func

def get_daemon():
    global _daemon
    if _daemon is None:
        try:
            from daemon import daemon_instance
            _daemon = daemon_instance
        except Exception:
            _daemon = None
    return _daemon


# ===========================================================================
# WINDOW DIMENSIONS & CORNER POSITIONING
# ===========================================================================
FULL_WIDTH = 380
FULL_HEIGHT = 570
ORB_WIDTH = 92
ORB_HEIGHT = 92
MARGIN_X = 20
MARGIN_Y = 54  # Floating nicely above standard Windows taskbar


class FridayWidgetApi:
    """Python API exposed directly to JavaScript inside the WebView."""

    def __init__(self):
        self.window = None
        self.audio_drive = True
        self.is_collapsed = False
        self.is_expanded = False
        self.is_visible = True
        self.screen_width = 1366
        self.screen_height = 768

    def set_window(self, window, sw, sh):
        self.window = window
        self.screen_width = sw
        self.screen_height = sh

    def send_query(self, query: str) -> str:
        """Processes user prompt through Brain and returns the response."""
        if not query or not query.strip():
            return "Sir, I did not receive any input."

        q = query.strip()
        daemon = get_daemon()
        if daemon:
            daemon.record_user_activity()

        # 0. Immediately interrupt any previous speech or alert before processing new directive
        try:
            from speak import interrupt_speech
            interrupt_speech()
        except Exception:
            pass

        # 1. Trigger Instant Zero-Silence Filler Audio
        if self.audio_drive:
            try:
                filler_fn = get_instant_filler()
                filler_fn(q, audio_enabled=True)
            except Exception:
                pass

        # 2. Tool callback to update UI in real-time
        def on_tool_call(tool_name, args):
            try:
                if self.window:
                    clean_args = {}
                    if isinstance(args, dict):
                        for k, v in args.items():
                            clean_args[k] = str(v)[:60]
                    js_code = f"window.fridayOnToolStart && window.fridayOnToolStart({json.dumps(tool_name)}, {json.dumps(clean_args)});"
                    self.window.evaluate_js(js_code)
            except Exception:
                pass

        # 3. Process via F.R.I.D.A.Y Cognitive Brain
        try:
            brain_fn = get_brain()
            response = brain_fn(q, origin='server', tool_callback=on_tool_call)
        except Exception as err:
            response = f"⚠️ System Exception in Brain: {err}"

        # Clean tool execution ticker in UI
        try:
            if self.window:
                self.window.evaluate_js("window.fridayOnToolEnd && window.fridayOnToolEnd();")
        except Exception:
            pass

        # 4. Speak response sequentially via centralized Speech Queue
        if self.audio_drive and response:
            clean_speech = response.replace("*", "").replace("`", "")
            speak_fn = get_speak()
            try:
                speak_fn(clean_speech, priority=1, allow_interrupt=True, block=False)
            except Exception:
                threading.Thread(target=speak_fn, args=(clean_speech,), daemon=True).start()

        return response or "Directive executed successfully, Sir."

    def start_voice_input(self) -> str:
        """Invokes speech recognition for voice command, interrupting ongoing speech first."""
        try:
            from speak import interrupt_speech
            interrupt_speech()
        except Exception:
            pass
        try:
            recog_fn = get_speech_recog()
            recognized = recog_fn(timeout=6, phrase_time_limit=9)
            return recognized if recognized else ""
        except Exception:
            return ""

    def interrupt_speech(self):
        """Immediately interrupts and silences all ongoing and queued speech."""
        try:
            from speak import interrupt_speech
            interrupt_speech()
        except Exception:
            pass
        return {"status": "interrupted"}

    def toggle_audio(self, is_active: bool):
        """Toggles TTS speaking responses on or off."""
        self.audio_drive = bool(is_active)
        daemon = get_daemon()
        if daemon:
            daemon.notify_voice = self.audio_drive
        return {"status": "ok", "audio_drive": self.audio_drive}

    def minimize_to_orb(self):
        """Collapses window down to a floating Siri orb in the corner."""
        if not self.window:
            return
        self.was_expanded = getattr(self, 'is_expanded', False)
        self.is_collapsed = True
        orb_x = self.screen_width - ORB_WIDTH - MARGIN_X
        orb_y = self.screen_height - ORB_HEIGHT - MARGIN_Y
        self.window.resize(ORB_WIDTH, ORB_HEIGHT)
        self.window.move(orb_x, orb_y)
        return {"mode": "orb"}

    def expand_to_full(self):
        """Expands window back up to full interactive HUD panel."""
        if not self.window:
            return
        self.is_collapsed = False
        self.is_expanded = getattr(self, 'was_expanded', False)
        if self.is_expanded:
            exp_w = min(780, self.screen_width - 40)
            exp_h = min(660, self.screen_height - 70)
            exp_x = self.screen_width - exp_w - MARGIN_X
            exp_y = self.screen_height - exp_h - MARGIN_Y
            self.window.resize(exp_w, exp_h)
            self.window.move(exp_x, exp_y)
            return {"mode": "expanded"}
        else:
            full_x = self.screen_width - FULL_WIDTH - MARGIN_X
            full_y = self.screen_height - FULL_HEIGHT - MARGIN_Y
            self.window.resize(FULL_WIDTH, FULL_HEIGHT)
            self.window.move(full_x, full_y)
            return {"mode": "full"}

    def toggle_expand_window(self):
        """Toggles between compact corner HUD (380x570) and enlarged HUD (780x660)."""
        if not self.window:
            return {"expanded": False}

        self.is_collapsed = False
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            exp_w = min(780, self.screen_width - 40)
            exp_h = min(660, self.screen_height - 70)
            exp_x = self.screen_width - exp_w - MARGIN_X
            exp_y = self.screen_height - exp_h - MARGIN_Y
            self.window.resize(exp_w, exp_h)
            self.window.move(exp_x, exp_y)
            return {"expanded": True, "width": exp_w, "height": exp_h}
        else:
            norm_x = self.screen_width - FULL_WIDTH - MARGIN_X
            norm_y = self.screen_height - FULL_HEIGHT - MARGIN_Y
            self.window.resize(FULL_WIDTH, FULL_HEIGHT)
            self.window.move(norm_x, norm_y)
            return {"expanded": False, "width": FULL_WIDTH, "height": FULL_HEIGHT}

    def hide_window(self):
        """Hides the widget window."""
        if self.window:
            self.window.hide()
            self.is_visible = False
        return {"visible": False}

    def show_window(self):
        """Restores and brings the widget to the foreground."""
        if self.window:
            self.window.show()
            self.window.restore()
            self.is_visible = True
        return {"visible": True}

    def close_application(self):
        """Cleanly shuts down all background processes and terminates the desktop application."""
        print("🛑 [F.R.I.D.A.Y] Close requested from UI. Shutting down all systems...", flush=True)
        try:
            self.stop_wake_word_listener()
            self.stop_live_mode()
        except Exception:
            pass

        try:
            d = get_daemon()
            if d:
                d.stop()
        except Exception:
            pass

        try:
            from utiles import load_memory
            from memory_controller import save_session_summary
            memory = load_memory()
            history = memory.get("conversation_history", [])
            save_session_summary(history)
        except Exception:
            pass

        def shutdown():
            time.sleep(0.1)
            try:
                if self.window:
                    self.window.destroy()
            except Exception:
                pass
            os._exit(0)

        threading.Thread(target=shutdown, daemon=True).start()
        return {"status": "closing"}

    def get_system_info(self) -> dict:
        """Returns battery, CPU, and system telemetry."""
        batt_str = "Optimal"
        try:
            from Tools.systems_tools import get_battery_status
            batt = get_battery_status()
            if isinstance(batt, dict) and "battery_percentage" in batt:
                batt_str = f"{batt['battery_percentage']}%"
        except Exception:
            pass

        return {
            "battery": batt_str,
            "status": "SYSTEM NOMINAL",
            "audio_drive": self.audio_drive,
            "is_expanded": self.is_expanded
        }

    def get_assistant_settings(self) -> dict:
        """Returns assistant configuration settings."""
        try:
            from config_driver import load_data
            data = load_data()
        except Exception:
            data = {}

        defaults = {
            "voice_enabled": self.audio_drive,
            "voice_speed": 185,
            "voice_pitch": 50,
            "sound_effects": True,
            "wake_word_active": True,
            "wake_word": "Hey Friday",
            "personality": "Stark Neural AI",
            "glow_theme": "cyan",
            "hotkey": "Ctrl + Space"
        }
        widget_settings = data.get("WIDGET_SETTINGS", defaults)
        # Ensure fallback keys
        for k, v in defaults.items():
            if k not in widget_settings:
                widget_settings[k] = v
        widget_settings["voice_enabled"] = self.audio_drive
        return widget_settings

    def save_assistant_settings(self, new_settings: dict) -> dict:
        """Saves assistant settings to config file and applies them."""
        try:
            from config_driver import load_data, save_data
            data = load_data()
            if "WIDGET_SETTINGS" not in data:
                data["WIDGET_SETTINGS"] = {}
            data["WIDGET_SETTINGS"].update(new_settings)
            save_data(data)

            if "voice_enabled" in new_settings:
                self.toggle_audio(bool(new_settings["voice_enabled"]))

            return {"status": "success", "settings": data["WIDGET_SETTINGS"]}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_user_profile_data(self) -> dict:
        """Returns user profile information, memory entries, and system info."""
        try:
            from config_driver import Check_Keys
            name = Check_Keys("USER", "Name") or "Sir"
            email = Check_Keys("USER", "email") or "Not configured"
            phone = Check_Keys("USER", "phone_number") or ""
        except Exception:
            name = "Sir"
            email = "Not configured"
            phone = ""

        memories = {}
        try:
            from memory_controller import _load_user_profile
            memories = _load_user_profile()
        except Exception:
            pass

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "role": "Primary Operator // Stark Industries Admin",
            "memories": memories,
            "device": os.environ.get("COMPUTERNAME", "STARK-DESKTOP")
        }

    def save_user_profile_data(self, profile_data: dict) -> dict:
        """Updates user profile information in config."""
        try:
            from config_driver import update_config
            if "name" in profile_data:
                update_config("USER", "Name", profile_data["name"])
            if "email" in profile_data:
                update_config("USER", "email", profile_data["email"])
            if "phone" in profile_data:
                update_config("USER", "phone_number", profile_data["phone"])
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def add_user_memory(self, text: str, mem_type: str = "preference") -> dict:
        """Manually records a memory item into RAG and user profile."""
        try:
            from RAG import save_longterm_memory
            save_longterm_memory(
                text=text,
                memory_type=mem_type,
                tags=[mem_type, "manual_entry"],
                importance="high",
                source="widget_ui"
            )
            try:
                from memory_controller import _update_user_profile
                _update_user_profile([{"text": text, "type": mem_type, "importance": "high"}])
            except Exception:
                pass
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ---------------- OPERATING MODES & PROTOCOLS ---------------- #
    def set_operating_mode(self, mode: str) -> dict:
        """
        Shifts assistant operating mode:
        'text' | 'voice' | 'wakeword' | 'live_screen' | 'live_camera' | 'stop_live'
        """
        if mode == "wakeword":
            res = self.start_wake_word_listener()
            if res.get("status") in ["started", "already_running"]:
                self.current_mode = "wakeword"
                return {"status": "ok", "mode": "wakeword"}
            return {"status": "error", "message": res.get("message", "Microphone or listener unavailable")}

        elif mode == "text":
            self.stop_wake_word_listener()
            self.stop_live_mode()
            self.current_mode = "text"
            return {"status": "ok", "mode": "text"}

        elif mode == "voice":
            self.stop_wake_word_listener()
            self.stop_live_mode()
            self.current_mode = "voice"
            self.audio_drive = True
            return {"status": "ok", "mode": "voice"}

        elif mode in ["live_screen", "live_camera"]:
            self.stop_wake_word_listener()
            cam_mode = "screen" if mode == "live_screen" else "camera"
            res = self.start_live_mode(cam_mode)
            self.current_mode = mode
            return {"status": "ok", "mode": mode, "live_status": res}

        elif mode == "stop_live":
            self.stop_live_mode()
            self.current_mode = "text"
            return {"status": "ok", "mode": "text"}

        return {"status": "error", "message": f"Unknown mode: {mode}"}

    def get_operating_mode(self) -> dict:
        """Returns the current operational mode and protocol states."""
        return {
            "mode": getattr(self, "current_mode", "text"),
            "wakeword_active": bool(getattr(self, "wake_listener", None) and self.wake_listener._running),
            "live_active": bool(getattr(self, "live_process", None) and self.live_process.poll() is None),
            "audio_drive": self.audio_drive
        }

    def start_wake_word_listener(self):
        """Starts hands-free wake word listener in background."""
        if getattr(self, "wake_listener", None) and self.wake_listener._running:
            return {"status": "already_running"}

        def on_wake(phrase):
            print(f"⚡ [F.R.I.D.A.Y] Wake word detected: {phrase}", flush=True)
            try:
                self.show_window()
                if self.window:
                    clean_phrase = str(phrase).replace('"', '')
                    self.window.evaluate_js(f"window.fridayOnWakeWord && window.fridayOnWakeWord({json.dumps(clean_phrase)});\n")
            except Exception:
                pass

        try:
            from wake_word import WakeWordListener
            self.wake_listener = WakeWordListener(on_wake_word=on_wake)
            started = self.wake_listener.start()
            return {"status": "started" if started else "error"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def stop_wake_word_listener(self):
        """Stops background wake word listener."""
        try:
            if getattr(self, "wake_listener", None) and self.wake_listener._running:
                self.wake_listener.stop()
                self.wake_listener = None
                return {"status": "stopped"}
        except Exception:
            pass
        self.wake_listener = None
        return {"status": "not_running"}

    def start_live_mode(self, video_mode: str = "screen"):
        """Starts Live Multimodal Vision Mode (Screen or Camera)."""
        self.stop_live_mode()
        try:
            import subprocess
            live_script = os.path.join(BASE_DIR, "Live_mode.py")
            self.live_process = subprocess.Popen([sys.executable, live_script, "--mode", video_mode])
            return {"status": "running", "mode": video_mode}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def stop_live_mode(self):
        """Terminates active live vision process."""
        if getattr(self, "live_process", None):
            try:
                self.live_process.terminate()
                self.live_process.wait(timeout=2)
            except Exception:
                try:
                    self.live_process.kill()
                except Exception:
                    pass
            self.live_process = None
            return {"status": "stopped"}
        return {"status": "not_running"}

    # ---------------- EXECUTIVE BRIEFING & REMINDERS ---------------- #
    def trigger_morning_briefing(self) -> str:
        """Generates proactive executive morning briefing."""
        try:
            daemon = get_daemon()
            if daemon:
                briefing = daemon.trigger_morning_briefing()
            else:
                from Tools.systems_tools import greet
                briefing = f"{greet()} Sir. All cognitive systems nominal."
        except Exception as e:
            briefing = f"Executive briefing note: {e}"

        if self.audio_drive and briefing:
            clean_speech = briefing.replace("*", "").replace("`", "")
            speak_fn = get_speak()
            threading.Thread(target=speak_fn, args=(clean_speech,), daemon=True).start()

        return briefing

    def get_reminders_and_tasks(self) -> dict:
        """Returns active reminders and todo tasks."""
        reminders = []
        tasks = []
        try:
            from Tools.reminder import list_reminders
            r_res = list_reminders()
            if isinstance(r_res, dict) and "reminders" in r_res:
                reminders = r_res["reminders"]
            elif isinstance(r_res, list):
                reminders = r_res
        except Exception:
            pass

        try:
            from Tools.Todo import list_tasks
            t_res = list_tasks()
            if isinstance(t_res, dict) and "tasks" in t_res:
                tasks = t_res["tasks"]
            elif isinstance(t_res, list):
                tasks = t_res
        except Exception:
            pass

        return {"reminders": reminders, "tasks": tasks}

    def add_reminder(self, reminder_text: str, remind_at: str) -> dict:
        """Adds a reminder."""
        try:
            from Tools.reminder import add_reminder
            res = add_reminder(reminder_text, remind_at)
            return {"status": "success", "result": res}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def add_task(self, task_text: str) -> dict:
        """Adds a todo task."""
        try:
            from Tools.Todo import add_task
            res = add_task(task_text)
            return {"status": "success", "result": res}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ---------------- CONFIG & API KEYS ---------------- #
    def get_api_keys_config(self) -> dict:
        """Returns API keys and model configuration from config.json."""
        try:
            from config_driver import load_data
            data = load_data()
            return {
                "keys": data.get("KEYS", {}),
                "llm": data.get("LLM", {}),
                "user": data.get("USER", {})
            }
        except Exception as e:
            return {"error": str(e)}

    def save_api_keys_config(self, new_config: dict) -> dict:
        """Saves API keys and LLM settings to config.json."""
        try:
            from config_driver import load_data, save_data
            data = load_data()
            if "keys" in new_config and isinstance(new_config["keys"], dict):
                data.setdefault("KEYS", {}).update(new_config["keys"])
            if "llm" in new_config and isinstance(new_config["llm"], dict):
                data.setdefault("LLM", {}).update(new_config["llm"])
            save_data(data)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


def get_screen_dimensions():
    """Detects primary screen width and height on Windows."""
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    except Exception:
        return 1366, 768


def run_widget_app():
    """Main launcher for F.R.I.D.A.Y Corner Widget."""
    # Compute screen corner positioning
    sw, sh = get_screen_dimensions()
    init_x = sw - FULL_WIDTH - MARGIN_X
    init_y = sh - FULL_HEIGHT - MARGIN_Y

    html_path = os.path.join(BASE_DIR, "widget_ui", "index.html")

    # Create Bridge API
    api = FridayWidgetApi()

    # Create Frameless Floating Transparent Window
    window = webview.create_window(
        title="F.R.I.D.A.Y // Neural Assistant",
        url=html_path,
        js_api=api,
        width=FULL_WIDTH,
        height=FULL_HEIGHT,
        x=init_x,
        y=init_y,
        resizable=False,
        frameless=True,
        easy_drag=True,
        on_top=True,
        background_color="#000000",
        transparent=True,
    )
    api.set_window(window, sw, sh)

    # Register real-time Speech Start / Speech End callbacks to drive crazy HUD visualizer
    def _on_speech_start(text):
        try:
            if api.window:
                preview = (text or "")[:80]
                api.window.evaluate_js(f"window.fridayOnSpeechStart && window.fridayOnSpeechStart({json.dumps(preview)});")
        except Exception:
            pass

    def _on_speech_end(interrupted=False):
        try:
            if api.window:
                api.window.evaluate_js(f"window.fridayOnSpeechEnd && window.fridayOnSpeechEnd({json.dumps(bool(interrupted))});")
        except Exception:
            pass

    try:
        from speak import register_speech_callback
        register_speech_callback(on_start=_on_speech_start, on_end=_on_speech_end)
    except Exception:
        pass

    # Global Hotkey Toggle Handler (Ctrl + Space)
    def toggle_widget():
        try:
            if api.is_visible:
                api.hide_window()
            else:
                api.show_window()
        except Exception:
            pass

    # 1. Register global keyboard hotkey via keyboard module
    try:
        keyboard.add_hotkey('ctrl+space', toggle_widget)
        print("⚡ [F.R.I.D.A.Y] Global hotkey registered: Ctrl + Space", flush=True)
    except Exception as e:
        print(f"⚠️ Hotkey registration note: {e}", flush=True)

    # 2. Register native Win32 RegisterHotKey fallback loop
    def win32_hotkey_listener():
        try:
            import win32con
            user32 = ctypes.windll.user32
            HOTKEY_ID = 101
            # MOD_CONTROL = 0x0002, VK_SPACE = 0x20
            if user32.RegisterHotKey(None, HOTKEY_ID, win32con.MOD_CONTROL, win32con.VK_SPACE):
                msg = wintypes.MSG()
                while user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
                    if msg.message == win32con.WM_HOTKEY and msg.wParam == HOTKEY_ID:
                        toggle_widget()
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageA(ctypes.byref(msg))
        except Exception:
            pass

    threading.Thread(target=win32_hotkey_listener, daemon=True).start()

    # 3. Start background Sentinel Daemon in separate thread
    def start_bg_daemon():
        d = get_daemon()
        if d:
            d.start()
    threading.Thread(target=start_bg_daemon, daemon=True).start()

    print(f"🚀 [F.R.I.D.A.Y] Floating Widget initialized at corner ({init_x}, {init_y}).", flush=True)
    print("Press Ctrl + Space anywhere on Windows to toggle the widget.", flush=True)

    try:
        # Start PyWebView loop (Edge WebView2)
        webview.start(debug=False)
    finally:
        # Save episodic memory on close
        try:
            from utiles import load_memory
            from memory_controller import save_session_summary
            memory = load_memory()
            history = memory.get("conversation_history", [])
            save_session_summary(history)
        except Exception:
            pass
        d = get_daemon()
        if d:
            d.stop()
        print("🟢 [F.R.I.D.A.Y] Widget shut down cleanly.", flush=True)


if __name__ == "__main__":
    run_widget_app()
