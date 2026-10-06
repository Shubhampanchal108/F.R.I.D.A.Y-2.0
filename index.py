import os
import sys
import time
import warnings
import logging

# ================================================================
# SILENCE TELEMETRY & NOISY THIRD-PARTY LOGGERS
# ================================================================
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_LOG_LEVEL"] = "ERROR"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.ERROR)
for logger_name in [
    "chromadb", "urllib3", "httpx", "httpcore", "openai",
    "sentence_transformers", "transformers", "speech_recognition"
]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import msvcrt
except ImportError:
    msvcrt = None

try:
    import winsound
except ImportError:
    winsound = None

from Brain import Brain
from voice_input import SpeechRecognition
from speak import speak
from wake_word import WakeWordListener
from Tools.systems_tools import greet
from config_driver import Check_Keys, is_agent_configured, run_first_time_setup, interactive_config_editor

from cli_interface import FridayCLI, console
from daemon import daemon_instance
from memory_controller import save_session_summary, get_last_session_context
from utiles import load_memory
from instant_filler import trigger_instant_filler

VOICE_COMMANDS = ["switch to voice", "voice mode", "/voice"]
TYPE_COMMANDS = ["switch to typing", "type mode", "/type"]
WAKE_COMMANDS = ["/wakeword", "wakeword", "wake word mode", "switch to wake word", "hands free"]
LIVE_COMMANDS = [
    "/live", "/vision", "live mode", "vision mode",
    "switch to live mode", "activate live mode", "start live mode",
    "switch to vision mode", "activate vision mode", "start vision mode",
    "/live screen", "/live camera", "/vision screen", "/vision camera"
]



def clean_query_text(query: str) -> str:
    """Strip leading, trailing, or embedded wake-word tokens from query."""
    q = query.strip()
    prefixes = [
        "hey friday", "ok friday", "okay friday", "hello friday", "hi friday",
        "listen friday", "friday", "fry day"
    ]
    q_lower = q.lower()
    for p in prefixes:
        if q_lower.startswith(p):
            cleaned = q[len(p):].lstrip(" ,:-").strip()
            if cleaned:
                return cleaned
        if q_lower.endswith(p):
            cleaned = q[:-len(p)].rstrip(" ,:-").strip()
            if cleaned:
                return cleaned

    # Check word-by-word if 'friday' or phonetic variant is inside the sentence
    words = q.split()
    target_words = {"friday", "fryday", "freeday", "fraiday", "frida", "fridey"}
    filtered = [w for w in words if w.lower().strip(".,!?\"'") not in target_words]
    if filtered:
        return " ".join(filtered)
    return q


def main():
    # ===== FIRST-TIME CONFIGURATION CHECK =====
    if not is_agent_configured():
        run_first_time_setup()

    AUTH_PASSWORD = Check_Keys("KEYS", "AGENT_PASSWORD")
    cli = FridayCLI(daemon=daemon_instance)
    wake_listener = WakeWordListener()

    # ===== AUTHENTICATION PANEL =====
    cli.print_banner()
    console.print("\n[bold yellow]🔒 Security Authentication Required[/bold yellow]")

    attempts = 0
    while True:
        password = console.input("[bold white]Enter Password:[/bold white] ", password=True)

        if password == AUTH_PASSWORD:
            console.print("✅ [bold green]Authentication successful! Welcome back, Sir.[/bold green]\n")
            break
        else:
            attempts += 1
            console.print("[bold red]❌ Access Denied. Incorrect password.[/bold red]\n")
            if attempts >= 3:
                console.print("[bold red]Too many failed attempts. Exiting.[/bold red]")
                sys.exit(1)

    # ===== START BACKGROUND DAEMON =====
    daemon_instance.start()

    # ===== INITIAL PROACTIVE EXECUTIVE BRIEFING =====
    greeting = greet()
    cli.print_banner()
    
    startup_batt = "optimal"
    try:
        from Tools.systems_tools import get_battery_status
        from Tools.Date_Time import get_current_time
        batt = get_battery_status()
        if isinstance(batt, dict) and "battery_percentage" in batt:
            startup_batt = f"{batt['battery_percentage']}%"
    except Exception:
        pass

    startup_msg = f"**{greeting}** Systems nominal. Battery is at {startup_batt}. Proactive Sentinel and Zero-Silence active. How may I assist you today, Sir?"
    cli.render_agent_response(startup_msg)

    if cli.audio_drive:
        speak(f"{greeting} Systems nominal, battery is at {startup_batt}. How may I assist you today, Sir?")

    # Cross-session continuity — show what happened last time
    try:
        last_context = get_last_session_context()
        if last_context:
            continuity_msg = f"By the way Sir, last time we were discussing: {last_context}"
            cli.render_agent_response(continuity_msg)
            if cli.audio_drive:
                speak(continuity_msg)
    except Exception:
        pass

    # ===== MAIN INTERACTIVE LOOP =====
    try:
        while True:
            query = ""

            # --- INPUT METHOD ---
            if cli.wake_protocol:
                console.print("[dim cyan]⚡ Hands-Free Standby: Say 'Friday' or press any key to type...[/dim cyan]")
                
                # Wait for either wake word detection OR keyboard input
                while not wake_listener.is_triggered():
                    if msvcrt and msvcrt.kbhit():
                        ch = msvcrt.getwch()
                        if ch in ['\r', '\n']:
                            query = console.input("\n[bold green]👤 You:[/bold green] ")
                        elif ord(ch) == 3:  # Ctrl+C
                            raise KeyboardInterrupt
                        else:
                            query = console.input(f"\n[bold green]👤 You:[/bold green] {ch}")
                            query = ch + query
                        break
                    time.sleep(0.08)

                if wake_listener.is_triggered():
                    detected_phrase = wake_listener.last_detected_text
                    wake_listener.clear_trigger()
                    has_wake, direct_cmd = wake_listener.extract_command(detected_phrase)

                    if direct_cmd and len(direct_cmd.strip()) > 1:
                        # ⚡ One-shot direct execution: user said "Friday <query>" in one sentence!
                        if winsound:
                            try:
                                winsound.Beep(1200, 120)
                            except Exception:
                                pass
                        console.print(f"\n[bold cyan]⚡ Direct Command Detected:[/bold cyan] [white]'{detected_phrase}'[/white]")
                        query = direct_cmd
                        cli.render_user_prompt(f"(Voice) {query}")
                    else:
                        # ⚡ Two-step wake-word: user only said "Friday" or "Hey Friday"
                        if winsound:
                            try:
                                winsound.Beep(1200, 150)
                            except Exception:
                                pass
                        console.print("\n[bold cyan]⚡ Wake-Word Detected! Listening for command...[/bold cyan]")
                        if cli.audio_drive:
                            speak("Yes Sir?")

                        with cli.spinner_task("F.R.I.D.A.Y Listening to Voice Command..."):
                            query = SpeechRecognition(timeout=6, phrase_time_limit=10)

                        if query:
                            cli.render_user_prompt(f"(Voice) {query}")
                        else:
                            console.print("[dim yellow]No command detected. Returning to wake-word standby...[/dim yellow]")
                            continue

            elif cli.vocal_protocol:
                console.print("\n[bold cyan]🎙️ Listening...[/bold cyan]")
                try:
                    with cli.spinner_task("F.R.I.D.A.Y Listening..."):
                        query = SpeechRecognition(timeout=6, phrase_time_limit=10)
                    if query:
                        cli.render_user_prompt(f"(Voice) {query}")
                except Exception as e:
                    console.print(f"[dim red]🎤 Mic Error: {e}[/dim red]")
                    continue
            else:
                try:
                    query = console.input("\n[bold green]👤 You:[/bold green] ")
                except (KeyboardInterrupt, EOFError):
                    break

            if not query or not query.strip():
                continue

            daemon_instance.record_user_activity()

            query_lower = query.lower().strip()

            # --- SLASH / PROTOCOL COMMANDS ---
            if query_lower in ["/exit", "exit", "quit", "goodbye"]:
                cli.render_agent_response("Goodbye Sir. Saving session memory and shutting down.")
                if cli.audio_drive:
                    speak("Goodbye Sir. Have a productive day.")
                # Save session summary as episodic memory before exit
                try:
                    memory = load_memory()
                    history = memory.get("conversation_history", [])
                    save_session_summary(history)
                except Exception:
                    pass
                break

            if query_lower in ["/help", "help"]:
                cli.print_help()
                continue

            if query_lower in ["/clear", "clear"]:
                cli.print_banner()
                continue

            if query_lower in ["/status", "status"]:
                cli.show_status()
                continue

            if query_lower in ["/reminders", "reminders"]:
                cli.show_reminders()
                continue

            if query_lower in ["/briefing", "briefing"]:
                briefing_res = daemon_instance.trigger_morning_briefing()
                cli.render_agent_response(briefing_res)
                continue

            if any(cmd == query_lower for cmd in WAKE_COMMANDS):
                cli.wake_protocol = not cli.wake_protocol
                if cli.wake_protocol:
                    cli.vocal_protocol = False
                    cli.type_protocol = False
                    started = wake_listener.start()
                    cli.print_banner()
                    if started:
                        msg = "Hands-Free Wake-Word Detector Active ⚡ Say **'Friday'** or **'Hey Friday'**."
                        cli.render_agent_response(msg)
                        if cli.audio_drive:
                            speak("Hands-free wake-word detector activated.")
                    else:
                        cli.wake_protocol = False
                        cli.type_protocol = True
                        cli.render_agent_response("⚠️ Microphone unavailable. Reverting to typing mode.")
                else:
                    cli.type_protocol = True
                    wake_listener.stop()
                    cli.print_banner()
                    cli.render_agent_response("Hands-Free Wake-Word Deactivated 🔇 Reverted to Typing Mode ⌨️")
                    if cli.audio_drive:
                        speak("Wake word detector deactivated.")
                continue

            if query_lower in ["/config", "config"]:
                interactive_config_editor()
                cli.print_banner()
                continue

            # --- LIVE MULTIMODAL VISION MODE PROTOCOL ---
            if (
                any(cmd == query_lower for cmd in LIVE_COMMANDS)
                or query_lower.startswith("/live")
                or query_lower.startswith("/vision")
            ):
                if "camera" in query_lower or "webcam" in query_lower:
                    chosen_mode = "camera"
                elif "screen" in query_lower or "desktop" in query_lower:
                    chosen_mode = "screen"
                else:
                    console.print("\n[bold bright_cyan]👁️ Select Live Vision Visual Feed:[/bold bright_cyan]")
                    console.print("  [bold green][1][/bold green] 🖥️ Screen Live Feed [dim](Real-time screen reading & UI analysis)[/dim] [bold cyan][Default][/bold cyan]")
                    console.print("  [bold green][2][/bold green] 📷 Webcam Camera Feed [dim](Real-life camera vision)[/dim]")
                    sel = console.input("[bold white]Select feed [1/2, Enter for Screen]: [/bold white]").strip()
                    chosen_mode = "camera" if sel == "2" else "screen"

                was_wake = cli.wake_protocol
                if was_wake:
                    wake_listener.stop()
                    cli.wake_protocol = False

                if cli.audio_drive:
                    speak(f"Activating live {'camera' if chosen_mode == 'camera' else 'screen'} mode, Sir.")

                try:
                    import importlib
                    import Live_mode
                    importlib.reload(Live_mode)
                    Live_mode.run_live_mode(video_mode=chosen_mode)
                except Exception as live_err:
                    console.print(f"[bold red]❌ Live Mode Error: {live_err}[/bold red]")
                finally:
                    if was_wake:
                        wake_listener.start()
                        cli.wake_protocol = True
                    cli.print_banner()
                    cli.render_agent_response("Live Vision Protocol Deactivated. Returned to standard mode, Sir.")
                    if cli.audio_drive:
                        speak("Live vision mode deactivated. How may I assist you now, Sir?")
                continue


            if any(cmd in query_lower for cmd in VOICE_COMMANDS):
                if cli.wake_protocol:
                    wake_listener.stop()
                    cli.wake_protocol = False
                cli.vocal_protocol = True
                cli.type_protocol = False
                cli.print_banner()
                cli.render_agent_response("Vocal Sense Protocol Activated 🎙️")
                if cli.audio_drive:
                    speak("Vocal sense protocol activated")
                continue

            if any(cmd in query_lower for cmd in TYPE_COMMANDS):
                if cli.wake_protocol:
                    wake_listener.stop()
                    cli.wake_protocol = False
                cli.vocal_protocol = False
                cli.type_protocol = True
                cli.print_banner()
                cli.render_agent_response("Type Assist Protocol Activated ⌨️")
                if cli.audio_drive:
                    speak("Type assist protocol activated")
                continue

            if ("off" in query_lower and "audio drive" in query_lower) or query_lower == "/audio":
                cli.audio_drive = not cli.audio_drive
                daemon_instance.notify_voice = cli.audio_drive
                status_msg = f"Audio Drive Protocol {'Activated 🔊' if cli.audio_drive else 'Deactivated 🔇'}"
                cli.render_agent_response(status_msg)
                if cli.audio_drive:
                    speak("Audio drive activated.")
                continue

            # --- PROCESS QUERY VIA AGENT BRAIN ---
            clean_query = clean_query_text(query)

            # ⚡ ZERO-SILENCE INSTANT AUDIO ACKNOWLEDGMENT (<10ms)
            if cli.audio_drive:
                trigger_instant_filler(clean_query, audio_enabled=True)

            def tool_status_callback(tool_name, args):
                cli.render_tool_call(tool_name, args)

            with cli.spinner_task("F.R.I.D.A.Y Processing & Executing Tools..."):
                try:
                    response = Brain(clean_query, origin='server', tool_callback=tool_status_callback)
                except Exception as err:
                    response = f"⚠️ System Exception in Brain loop: {err}"

            if response:
                final_ans = response.replace("*", "")
                cli.render_agent_response(final_ans)

                if cli.audio_drive:
                    speak(final_ans)

    finally:
        # Stop background listeners
        try:
            wake_listener.stop()
        except Exception:
            pass

        # Save session summary on any exit (including Ctrl+C)
        try:
            memory = load_memory()
            history = memory.get("conversation_history", [])
            save_session_summary(history)
        except Exception:
            pass

        # Shutdown daemon cleanly on exit
        daemon_instance.stop()
        console.print("\n[dim cyan]🟢 F.R.I.D.A.Y Daemon and CLI shut down cleanly. Good day, Sir![/dim cyan]")


if __name__ == "__main__":
    main()
