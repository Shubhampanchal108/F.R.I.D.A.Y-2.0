import sys
import os
import time

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from Brain import Brain
from voice_input import SpeechRecognition
from speak import speak
from Tools.systems_tools import greet
from config_driver import Check_Keys, is_agent_configured, run_first_time_setup, interactive_config_editor

from cli_interface import FridayCLI, console
from daemon import daemon_instance
from memory_controller import save_session_summary, get_last_session_context
from utiles import load_memory

VOICE_COMMANDS = ["switch to voice", "voice mode", "/voice"]
TYPE_COMMANDS = ["switch to typing", "type mode", "/type"]
STREAM_COMMANDS = ["switch to live stream", "stream mode", "/stream"]


def main():
    # ===== FIRST-TIME CONFIGURATION CHECK =====
    if not is_agent_configured():
        run_first_time_setup()

    AUTH_PASSWORD = Check_Keys("KEYS", "AGENT_PASSWORD")
    cli = FridayCLI(daemon=daemon_instance)
    
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
    
    # ===== INITIAL GREETING =====
    greeting = greet()
    cli.print_banner()
    cli.render_agent_response(f"**{greeting}** How may I assist you today, Sir?")
    
    if cli.audio_drive:
        speak(f"{greeting} How may I assist you, Sir?")

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
            if cli.vocal_protocol:
                console.print("\n[bold cyan]🎙️ Listening...[/bold cyan]")
                try:
                    query = SpeechRecognition()
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

            if query_lower in ["/wakeword", "wakeword"]:
                cli.render_agent_response("Hands-Free Wake-Word Detector active ('Friday' / 'Hey Friday') ⚡")
                continue

            if query_lower in ["/config", "config"]:
                interactive_config_editor()
                cli.print_banner()
                continue

            if any(cmd in query_lower for cmd in VOICE_COMMANDS):
                cli.vocal_protocol = True
                cli.type_protocol = False
                cli.print_banner()
                cli.render_agent_response("Vocal Sense Protocol Activated 🎙️")
                if cli.audio_drive:
                    speak("Vocal sense protocol activated")
                continue

            if any(cmd in query_lower for cmd in TYPE_COMMANDS):
                cli.vocal_protocol = False
                cli.type_protocol = True
                cli.print_banner()
                cli.render_agent_response("Type Assist Protocol Activated ⌨️")
                if cli.audio_drive:
                    speak("Type assist protocol activated")
                continue

            if "off" in query_lower and "audio drive" in query_lower or query_lower == "/audio":
                cli.audio_drive = not cli.audio_drive
                status_msg = f"Audio Drive Protocol {'Activated 🔊' if cli.audio_drive else 'Deactivated 🔇'}"
                cli.render_agent_response(status_msg)
                if cli.audio_drive:
                    speak("Audio drive activated.")
                continue

            # --- PROCESS QUERY VIA AGENT BRAIN ---
            clean_query = query_lower.replace("friday", "").strip()
            
            def tool_status_callback(tool_name, args):
                cli.print_agent_thought(f"Executing Tool: [bold yellow]{tool_name}[/bold yellow] {args if args else ''}")

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
