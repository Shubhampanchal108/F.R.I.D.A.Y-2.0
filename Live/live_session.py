"""
=============================================================================
F.R.I.D.A.Y LIVE MULTIMODAL // LIVE SESSION MANAGER
=============================================================================
Connects to Google Gemini Live WebSocket API, manages async task groups,
dispatches tool executions, and relays multimodal streams.
=============================================================================
"""

import os
import sys
import asyncio
import warnings
import logging
from dotenv import dotenv_values
from rich.console import Console

# Silence noisy SDK loggers & warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=UserWarning)
logging.getLogger("google.genai").setLevel(logging.ERROR)

from google import genai
from google.genai import types

from Live.tools_schema import get_live_tools
from Live.vision_stream import VisionStreamer
from Live.audio_stream import AudioStreamer
from Live.bridge import FridayBridge
from Tool_guard import execute_tool

console = Console()



LIVE_MODELS = [
    "models/gemini-2.5-flash-native-audio-latest",
    "models/gemini-2.5-flash-native-audio-preview-12-2025",
    "models/gemini-2.5-flash-native-audio-preview-09-2025",
    "models/gemini-3.8-live",
    "gemini-2.0-flash-exp"
]


def get_gemini_api_key():
    """Retrieve verified Google Gemini API key (must start with 'AIza')."""
    # 1. Local config.json under KEYS -> GEMINI_KEY
    try:
        from config_driver import load_data
        data = load_data()
        k = data.get("KEYS", {}).get("GEMINI_KEY")
        if k and str(k).strip().startswith("AIza"):
            return str(k).strip()
    except Exception:
        pass

    # 2. Environment variables
    for env_var in ["GEMINI_KEY", "GEMINI_API_KEY"]:
        k = os.environ.get(env_var)
        if k and str(k).strip().startswith("AIza"):
            return str(k).strip()

    # 3. JARVIS AI .env fallback
    try:
        jarvis_env_path = r"C:\Users\j\OneDrive\Desktop\shubham studio\JARVIS AI\Backend\.env"
        if os.path.exists(jarvis_env_path):
            envs = dotenv_values(jarvis_env_path)
            k = envs.get("GEMINI_KEY") or envs.get("GEMINI_API_KEY")
            if k and str(k).strip().startswith("AIza"):
                return str(k).strip()
    except Exception:
        pass

    # 4. Prompt via Check_Keys
    try:
        from config_driver import Check_Keys
        return Check_Keys("KEYS", "GEMINI_KEY")
    except Exception:
        return None


class LiveSession:
    """
    Manages the lifecycle of a Gemini Live multimodal conversation session.
    """

    def __init__(self, video_mode="screen"):
        self.video_mode = video_mode
        self.bridge = FridayBridge()
        self.vision = VisionStreamer()
        self.audio = AudioStreamer()

        self.session = None
        self.send_lock = asyncio.Lock()
        self.stop_event = asyncio.Event()

    async def send_text_loop(self):
        """
        Listens for text directives either from stdin (interactive CLI / IPC piped from UI)
        or bridge queue, and forwards them as user turns to Gemini Live.
        """
        while not self.stop_event.is_set():
            try:
                # Read from sys.stdin in a separate thread
                text = await asyncio.to_thread(sys.stdin.readline)
                if not text:
                    await asyncio.sleep(0.1)
                    continue

                text = text.strip()
                if not text:
                    continue

                clean_t = text.lower().strip()
                if clean_t in ["stop", "exit", "quit", "/exit", "/stop", "q", "back"]:
                    console.print("\n[bold yellow]🛑 Stopping Live Session...[/bold yellow]")
                    self.stop_event.set()
                    break

                # Record in shared Core Friday conversation memory & UI
                self.bridge.record_user_turn(text)

                async with self.send_lock:
                    await self.session.send_client_content(
                        turns=[types.Content(role="user", parts=[types.Part(text=text)])],
                        turn_complete=True
                    )
            except (asyncio.CancelledError, KeyboardInterrupt):
                break
            except Exception as e:
                if self.stop_event.is_set():
                    break
                await asyncio.sleep(0.05)

    async def receive_loop(self):
        """
        Handles inbound stream from Gemini Live:
        - Dequeues audio chunks
        - Safely extracts text without non-text parts warnings
        - Executes real-time tools
        - Synchronizes replies to Core Friday
        """
        new_turn = True
        turn_text_buffer = []

        try:
            while not self.stop_event.is_set():
                turn = self.session.receive()
                turn_text_buffer = []

                async for response in turn:
                    if self.stop_event.is_set():
                        break

                    # 1. Neural audio playback chunk
                    if data := response.data:
                        self.audio.audio_in_queue.put_nowait(data)

                    # 2. Text response parts & output transcription (safely extracted without non-text parts warnings)
                    text_chunk = None
                    if response.server_content and getattr(response.server_content, "model_turn", None):
                        for part in response.server_content.model_turn.parts:
                            if getattr(part, "text", None):
                                text_chunk = part.text
                                break
                    if not text_chunk and response.server_content and getattr(response.server_content, "output_transcription", None):
                        text_chunk = response.server_content.output_transcription.text

                    if text_chunk:
                        turn_text_buffer.append(text_chunk)
                        if new_turn:
                            console.print("\n[bold cyan]🤖 F.R.I.D.A.Y:[/bold cyan] ", end="", highlight=False)
                            new_turn = False
                        print(text_chunk, end="", flush=True)

                    # 3. User spoken voice transcription feedback (Gemini recognized speech)
                    if response.server_content and getattr(response.server_content, "input_transcription", None):
                        u_speech = response.server_content.input_transcription.text
                        if u_speech and u_speech.strip():
                            console.print(f"\n[bold green]👤 You (Spoken):[/bold green] {u_speech.strip()}", highlight=False)
                            self.bridge.record_user_turn(u_speech.strip())

                    # 3. Function Calling / Live Tool Execution
                    if tool_call := response.tool_call:
                        function_responses = []
                        for call in tool_call.function_calls:
                            tool_name = call.name
                            tool_args = call.args or {}
                            call_id = call.id

                            console.print(f"\n[bold cyan]⚡ Live Tool Executing:[/bold cyan] [bold yellow]{tool_name}[/bold yellow] [dim]({tool_args if tool_args else ''})[/dim]")
                            try:
                                res = await asyncio.to_thread(execute_tool, tool_name, "server", **tool_args)
                            except Exception as e:
                                res = {"error": str(e)}

                            console.print(f"[bold green]✔ Tool Completed:[/bold green] [dim]{str(res)[:100]}[/dim]")

                            res_payload = res if isinstance(res, dict) else {"result": str(res)}
                            function_responses.append(
                                types.FunctionResponse(
                                    name=tool_name,
                                    id=call_id,
                                    response=res_payload
                                )
                            )

                        if function_responses:
                            try:
                                async with self.send_lock:
                                    await self.session.send_tool_response(function_responses=function_responses)
                            except Exception as e:
                                console.print(f"[dim red]⚠️ Failed to send tool response: {e}[/dim red]")

                    if response.tool_call_cancellation:
                        console.print("[dim yellow]⚠️ Tool call was cancelled by model.[/dim yellow]")

                new_turn = True
                if turn_text_buffer:
                    full_reply = "".join(turn_text_buffer).strip()
                    if full_reply:
                        # Record response in shared Core Friday memory & emit token for UI
                        self.bridge.record_assistant_turn(full_reply)
                    turn_text_buffer = []

                # Clear remaining audio queue if needed
                while not self.audio.audio_in_queue.empty():
                    try:
                        self.audio.audio_in_queue.get_nowait()
                    except Exception:
                        break

        except asyncio.CancelledError:
            pass
        except Exception as e:
            if not self.stop_event.is_set():
                console.print(f"\n[dim red]⚠️ Receive notice: {e}[/dim red]")

    async def run(self):
        """Main connection and streaming loop."""
        api_key = get_gemini_api_key()
        if not api_key:
            console.print("[bold red]❌ Google Gemini API Key (starts with 'AIza') not found.[/bold red]")
            return

        client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=api_key,
        )

        system_instruction = self.bridge.get_unified_system_instruction()
        tools = get_live_tools()

        config = types.LiveConnectConfig(
            system_instruction=types.Content(parts=[types.Part(text=system_instruction)]),
            response_modalities=["AUDIO"],
            media_resolution="MEDIA_RESOLUTION_LOW",
            input_audio_transcription=types.AudioTranscriptionConfig(),
            generation_config=types.GenerationConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                temperature=0.7,
            ),
            tools=tools,
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
                )
            ),
            context_window_compression=types.ContextWindowCompressionConfig(
                trigger_tokens=16000,
                sliding_window=types.SlidingWindow(target_tokens=8000),
            ),
        )

        connected = False
        for current_model in LIVE_MODELS:
            try:
                console.print(f"[bold cyan]🔗 Connecting to Gemini Live ({current_model})...[/bold cyan]")
                self.bridge.emit_status("CONNECTING")

                async with (
                    client.aio.live.connect(model=current_model, config=config) as session,
                    asyncio.TaskGroup() as tg,
                ):
                    connected = True
                    self.session = session
                    self.bridge.emit_status("CONNECTED")

                    # Launch concurrent multimodal tasks
                    send_text_task = tg.create_task(self.send_text_loop())
                    tg.create_task(self.audio.listen_audio_loop(session, self.send_lock, self.stop_event))

                    if self.video_mode == "camera":
                        tg.create_task(self.vision.stream_camera(session, self.send_lock, self.stop_event))
                    elif self.video_mode == "screen":
                        tg.create_task(self.vision.stream_screen(session, self.send_lock, self.stop_event))

                    tg.create_task(self.receive_loop())
                    tg.create_task(self.audio.play_audio_loop(self.stop_event))

                    # Keep live session running continuously until stop_event is triggered
                    await self.stop_event.wait()
                    send_text_task.cancel()
                    break

            except (asyncio.CancelledError, KeyboardInterrupt):
                break
            except ExceptionGroup as eg:
                if connected:
                    for exc in eg.exceptions:
                        if not isinstance(exc, (asyncio.CancelledError, KeyboardInterrupt)):
                            console.print(f"\n[bold red]⚠️ Notice: {exc}[/bold red]")
                    break
                else:
                    console.print(f"[dim yellow]Model {current_model} connection error. Trying fallback...[/dim yellow]")
                    continue
            except Exception as e:
                if connected:
                    console.print(f"\n[bold red]⚠️ Live Mode Notice: {e}[/bold red]")
                    break
                else:
                    console.print(f"[dim yellow]Model {current_model} failed: {e}. Trying fallback...[/dim yellow]")
                    continue
        else:
            if not connected:
                console.print("[bold red]❌ Unable to connect to Gemini Live models. Please check your network and GEMINI_KEY.[/bold red]")

        self.stop_event.set()
        self.bridge.stop()
        self.bridge.emit_status("DISCONNECTED")
        self.audio.close()
