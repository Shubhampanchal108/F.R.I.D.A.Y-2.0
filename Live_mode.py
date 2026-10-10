import os
import sys
import asyncio
import io
import traceback
import argparse
import warnings

# Suppress noisy warnings
warnings.filterwarnings("ignore")

import cv2
import pyaudio
import PIL.Image
import mss

# UTF-8 stdout reconfigure for Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from google import genai
from google.genai import types
from dotenv import dotenv_values
from rich.console import Console
from rich.panel import Panel
from rich import box

# Parent directory for relative imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from Tool_guard import load_tools, execute_tool, TOOLS
from daemon import daemon_instance
registry = load_tools()

Friday_Details = (
    "You are F.R.I.D.A.Y (Friendly Reliable Intelligent Digital Assistant for Youth), created by Shubham sir. "
    "You are currently operating in LIVE MULTIMODAL STREAMING MODE. "
    "You can continuously see real-time visual frames (from the desktop screen or camera) and hear real-time audio from the user. "
    "Rules: "
    "1. Always address the user politely as 'Sir' or 'Shubham sir'. "
    "2. If asked about what is on screen or in front of the camera, describe it accurately, pointing out code, UI elements, errors, or objects. "
    "3. Keep spoken replies concise, natural, and conversational (around 1-3 sentences unless explaining a complex problem). "
    "4. Support both English and natural Hindi (Hinglish) based on user query. "
    "5. Do NOT output raw JSON or code tags in spoken audio. "
    "6. You have DIRECT access to live system tools (adjusting volume, brightness, battery check, launching apps, closing apps, taking screenshots, searching web, weather, tasks, reminders). When the user asks you to perform an action or check system information, CALL the corresponding tool immediately, and after receiving the result, inform the user concisely in natural voice. "
    "7. REAL-TIME DYNAMIC VISION: Visual frames are continuously streamed to you. ALWAYS observe and describe the CURRENT / MOST RECENT frame you received. Screens and camera scenes change dynamically — never assume an older screen or application is still active if the current frame shows a different window or scene."
)

# Function declarations for Gemini Live Multimodal Function Calling
LIVE_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "volume_up",
                "description": "Increase system audio volume by specified step percentage (default 10%).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "step": {"type": "INTEGER", "description": "Step percentage to increase (default 10)."}
                    }
                }
            },
            {
                "name": "volume_down",
                "description": "Decrease system audio volume by specified step percentage (default 10%).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "step": {"type": "INTEGER", "description": "Step percentage to decrease (default 10)."}
                    }
                }
            },
            {
                "name": "mute_volume",
                "description": "Mute system audio volume."
            },
            {
                "name": "unmute_volume",
                "description": "Unmute system audio volume."
            },
            {
                "name": "brightness_up",
                "description": "Increase screen brightness."
            },
            {
                "name": "brightness_down",
                "description": "Decrease screen brightness."
            },
            {
                "name": "check_battery",
                "description": "Check device battery percentage and charging status."
            },
            {
                "name": "check_cpu",
                "description": "Check device CPU usage percentage and core counts."
            },
            {
                "name": "open_app",
                "description": "Open a desktop application on Windows (e.g. chrome, notepad, calculator, spotify, vscode).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "app": {"type": "STRING", "description": "Name of the application to open."}
                    },
                    "required": ["app"]
                }
            },
            {
                "name": "close_app",
                "description": "Close an application or active window on Windows.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "app": {"type": "STRING", "description": "Name of application to close (optional)."}
                    }
                }
            },
            {
                "name": "capture_screenshot",
                "description": "Take a screenshot of the current screen and save it."
            },
            {
                "name": "open_website",
                "description": "Open a website URL or domain in the default web browser.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {"type": "STRING", "description": "Website URL or domain (e.g. youtube.com, github.com)."}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "minimize_active_window",
                "description": "Minimize the current active window."
            },
            {
                "name": "maximize_active_window",
                "description": "Maximize the current active window."
            },
            {
                "name": "clear_recycle_bin",
                "description": "Empty the Windows recycle bin."
            },
            {
                "name": "get_weather",
                "description": "Get current weather conditions for a city.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "city": {"type": "STRING", "description": "City or location name."}
                    },
                    "required": ["city"]
                }
            },
            {
                "name": "get_current_time",
                "description": "Get current local time."
            },
            {
                "name": "get_date_with_day",
                "description": "Get today's date and day of week."
            },
            {
                "name": "google_search",
                "description": "Search Google for current real-time information or questions.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Search query text."}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_wikipedia",
                "description": "Search Wikipedia for a topic summary.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Topic or query to look up on Wikipedia."}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "add_reminder",
                "description": "Schedule a reminder.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "reminder_text": {"type": "STRING", "description": "What to remind the user about."},
                        "remind_at": {"type": "STRING", "description": "Time to remind, e.g. '18:30' or '2 hours'."}
                    },
                    "required": ["reminder_text", "remind_at"]
                }
            },
            {
                "name": "list_reminders",
                "description": "List all active and pending reminders."
            },
            {
                "name": "add_task",
                "description": "Add a new task to the user to-do list.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_text": {"type": "STRING", "description": "Description of task to add."}
                    },
                    "required": ["task_text"]
                }
            },
            {
                "name": "list_tasks",
                "description": "List all active tasks in to-do list."
            },
            {
                "name": "youtube_automation",
                "description": "Search and play a video or music track on YouTube.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Name of song, artist, or video to play."}
                    },
                    "required": ["query"]
                }
            }
        ]
    }
]

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 800

LIVE_MODELS = [
    "models/gemini-2.5-flash-native-audio-latest",
    "models/gemini-2.5-flash-native-audio-preview-09-2025",
    "models/gemini-3.1-flash-live-preview",
    "gemini-2.0-flash-exp"
]
MODEL = LIVE_MODELS[0]
DEFAULT_MODE = "screen"

pya = pyaudio.PyAudio()
console = Console()


def get_gemini_api_key():
    """Retrieve verified Google Gemini API key (must start with 'AIza')."""
    # 1. Local config.json under GEMINI_KEY
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
                try:
                    from config_driver import update_config
                    update_config("KEYS", "GEMINI_KEY", str(k).strip())
                except Exception:
                    pass
                return str(k).strip()
    except Exception:
        pass

    # 4. Prompt via Check_Keys
    try:
        from config_driver import Check_Keys
        return Check_Keys("KEYS", "GEMINI_KEY")
    except Exception:
        return None


class AudioLoop:
    def __init__(self, video_mode=DEFAULT_MODE):
        self.video_mode = video_mode
        self.audio_in_queue = None
        self.session = None
        self.audio_stream = None
        self.output_stream = None
        self.send_lock = asyncio.Lock()

        # Flags for playback and termination
        self.is_playing = asyncio.Event()
        self.stop_event = asyncio.Event()

    async def send_text(self):
        # In GUI widget mode or non-interactive subshell without tty:
        if not sys.stdin or not hasattr(sys.stdin, "isatty") or not sys.stdin.isatty():
            await self.stop_event.wait()
            return

        while not self.stop_event.is_set():
            try:
                text = await asyncio.to_thread(input, "\n💬 You [speak or type / 'stop' to exit]: ")
            except (EOFError, KeyboardInterrupt):
                self.stop_event.set()
                break

            if not text or not text.strip():
                continue

            clean_t = text.lower().strip()
            if clean_t in ["stop", "exit", "quit", "/exit", "/stop", "q", "back"]:
                console.print("\n[bold yellow]🛑 Stopping Live Session...[/bold yellow]")
                self.stop_event.set()
                break

            try:
                async with self.send_lock:
                    await self.session.send_client_content(
                        turns=[types.Content(role="user", parts=[types.Part(text=text)])],
                        turn_complete=True
                    )
            except Exception as e:
                console.print(f"[dim red]⚠️ Text notice: {e}[/dim red]")

    def _get_frame(self, cap):
        ret, frame = cap.read()
        if not ret or frame is None:
            return None
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)
        img.thumbnail([640, 480])

        image_io = io.BytesIO()
        img.save(image_io, format="JPEG", quality=55)
        return types.Blob(data=image_io.getvalue(), mime_type="image/jpeg")

    async def get_frames(self):
        cap = await asyncio.to_thread(cv2.VideoCapture, 0)
        if not cap.isOpened():
            console.print("\n[bold red]⚠️ Webcam could not be opened on device 0. Audio-only mode active.[/bold red]")
            return

        try:
            # Send initial webcam frame immediately
            init_blob = await asyncio.to_thread(self._get_frame, cap)
            if init_blob:
                try:
                    async with self.send_lock:
                        await self.session.send_realtime_input(media=init_blob)
                except Exception:
                    pass

            while not self.stop_event.is_set():
                await asyncio.sleep(1.0)
                if self.stop_event.is_set():
                    break

                blob = await asyncio.to_thread(self._get_frame, cap)
                if blob is None:
                    continue

                try:
                    async with self.send_lock:
                        await self.session.send_realtime_input(media=blob)
                except Exception:
                    if self.stop_event.is_set():
                        break
        finally:
            cap.release()

    def _get_screen(self):
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                i = sct.grab(monitor)
                img = PIL.Image.frombytes("RGB", i.size, i.rgb)
                img.thumbnail([640, 480])
                image_io = io.BytesIO()
                img.save(image_io, format="JPEG", quality=55)
                return types.Blob(data=image_io.getvalue(), mime_type="image/jpeg")
        except Exception:
            try:
                import PIL.ImageGrab
                img = PIL.ImageGrab.grab()
                img.thumbnail([640, 480])
                image_io = io.BytesIO()
                img.save(image_io, format="JPEG", quality=55)
                return types.Blob(data=image_io.getvalue(), mime_type="image/jpeg")
            except Exception:
                return None

    async def get_screen(self):
        # Send initial screen frame immediately
        init_blob = await asyncio.to_thread(self._get_screen)
        if init_blob:
            try:
                async with self.send_lock:
                    await self.session.send_realtime_input(media=init_blob)
            except Exception:
                pass

        while not self.stop_event.is_set():
            # Send clean, fresh screen frame every 1.5s (prevents token backlog)
            await asyncio.sleep(1.5)
            if self.stop_event.is_set():
                break

            blob = await asyncio.to_thread(self._get_screen)
            if blob is None:
                continue

            try:
                async with self.send_lock:
                    await self.session.send_realtime_input(media=blob)
            except Exception:
                if self.stop_event.is_set():
                    break

    async def listen_audio(self):
        try:
            mic_info = pya.get_default_input_device_info()
            self.audio_stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=SEND_SAMPLE_RATE,
                input=True,
                input_device_index=mic_info["index"],
                frames_per_buffer=CHUNK_SIZE,
            )
        except Exception as e:
            console.print(f"\n[bold red]⚠️ Microphone Init Error: {e}[/bold red]")
            return

        kwargs = {"exception_on_overflow": False}
        while not self.stop_event.is_set():
            try:
                # Read continuously to prevent hardware buffer accumulation / delay drift!
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)

                # While Friday speaks, discard mic input to prevent echo and backlog buildup
                if self.is_playing.is_set():
                    continue

                blob = types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                async with self.send_lock:
                    await self.session.send_realtime_input(media=blob)

            except Exception:
                if self.stop_event.is_set():
                    break
                await asyncio.sleep(0.01)

    async def receive_audio(self):
        new_turn = True
        turn_text_buffer = []
        try:
            while not self.stop_event.is_set():
                turn = self.session.receive()
                turn_text_buffer = []
                async for response in turn:
                    if self.stop_event.is_set():
                        break
                    if data := response.data:
                        self.audio_in_queue.put_nowait(data)
                    if text := response.text:
                        turn_text_buffer.append(text)
                        if new_turn:
                            console.print("\n[bold cyan]🤖 F.R.I.D.A.Y:[/bold cyan] ", end="", highlight=False)
                            new_turn = False
                        print(text, end="", flush=True)

                    # Handle Real-Time Tool Calls from Gemini Live
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

                            if isinstance(res, dict):
                                res_payload = res
                            else:
                                res_payload = {"result": str(res)}

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
                        try:
                            from utiles import add_to_history
                            add_to_history("assistant", full_reply)
                        except Exception:
                            pass
                        # Emit structured token for IPC listener
                        print(f"\n[LIVE_FEED_REPLY]: {full_reply}\n", flush=True)
                    turn_text_buffer = []

                while not self.audio_in_queue.empty():
                    try:
                        self.audio_in_queue.get_nowait()
                    except Exception:
                        break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if not self.stop_event.is_set():
                console.print(f"\n[dim red]⚠️ Receive notice: {e}[/dim red]")

    async def play_audio(self):
        try:
            self.output_stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
            )
        except Exception as e:
            console.print(f"\n[bold red]⚠️ Speaker Output Error: {e}[/bold red]")
            return

        while not self.stop_event.is_set():
            try:
                bytestream = await asyncio.wait_for(self.audio_in_queue.get(), timeout=0.2)
                self.is_playing.set()
                await asyncio.to_thread(self.output_stream.write, bytestream)
                if self.audio_in_queue.empty():
                    self.is_playing.clear()
            except asyncio.TimeoutError:
                continue
            except Exception:
                self.is_playing.clear()
                if self.stop_event.is_set():
                    break

    async def run(self):
        api_key = get_gemini_api_key()
        if not api_key:
            console.print("[bold red]❌ Google Gemini API Key (starts with 'AIza') not found.[/bold red]")
            return

        client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=api_key,
        )

        config = types.LiveConnectConfig(
            system_instruction=types.Content(parts=[types.Part(text=Friday_Details)]),
            response_modalities=["AUDIO"],
            media_resolution="MEDIA_RESOLUTION_MEDIUM",
            tools=LIVE_TOOLS,
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
                )
            ),
            context_window_compression=types.ContextWindowCompressionConfig(
                trigger_tokens=25600,
                sliding_window=types.SlidingWindow(target_tokens=12800),
            ),
        )

        connected = False
        for current_model in LIVE_MODELS:
            try:
                console.print(f"[bold cyan]🔗 Connecting to Gemini Live ({current_model})...[/bold cyan]")
                async with (
                    client.aio.live.connect(model=current_model, config=config) as session,
                    asyncio.TaskGroup() as tg,
                ):
                    connected = True
                    self.session = session
                    self.audio_in_queue = asyncio.Queue()

                    send_text_task = tg.create_task(self.send_text())
                    tg.create_task(self.listen_audio())

                    if self.video_mode == "camera":
                        tg.create_task(self.get_frames())
                    elif self.video_mode == "screen":
                        tg.create_task(self.get_screen())

                    tg.create_task(self.receive_audio())
                    tg.create_task(self.play_audio())

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
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except Exception:
                pass
        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
            except Exception:
                pass


def run_live_mode(video_mode="screen"):
    """
    Launch F.R.I.D.A.Y's Real-Time Live Multimodal Vision & Audio Protocol.
    video_mode: 'screen' (desktop screen reading) | 'camera' (webcam vision) | 'none' (audio-only)
    """
    mode_name = "🖥️ REAL-TIME SCREEN STREAM" if video_mode == "screen" else "📷 REAL-LIFE WEBCAM STREAM" if video_mode == "camera" else "🎙️ REAL-TIME AUDIO"

    live_panel = Panel(
        f"[bold bright_cyan]⚡ F.R.I.D.A.Y LIVE MULTIMODAL VISION SYSTEM ACTIVATED ⚡[/bold bright_cyan]\n\n"
        f"[bold white]Visual Mode:[/bold white] [bold bright_green]{mode_name}[/bold bright_green]\n"
        f"[bold white]Audio Stream:[/bold white] [bold bright_green]Bidirectional Real-Time Audio (Zephyr Neural Voice)[/bold bright_green]\n"
        f"[bold white]Live Tools:[/bold white] [bold bright_green]Active ⚡ (Volume, Apps, Screenshots, Battery, Web, Reminders)[/bold bright_green]\n"
        f"[bold white]Gemini Model:[/bold white] [dim]{MODEL}[/dim]\n\n"
        f"[bold yellow]Instructions:[/bold yellow]\n"
        f" • Speak directly into your microphone to talk to FRIDAY.\n"
        f" • Friday can see your {'screen in real time' if video_mode == 'screen' else 'webcam in real time'}.\n"
        f" • Friday can execute system actions (open apps, screenshots, volume, battery, etc.) in real time.\n"
        f" • Type [bold red]'stop'[/bold red] or [bold red]'exit'[/bold red] or press [bold red]Ctrl+C[/bold red] to return to FRIDAY HUD.",
        title="[bold magenta]👁️ F.R.I.D.A.Y VISION HUB 👁️[/bold magenta]",
        box=box.DOUBLE,
        border_style="bright_magenta"
    )
    console.print(live_panel)

    loop = AudioLoop(video_mode=video_mode)
    try:
        asyncio.run(loop.run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Live session stopped by user (Ctrl+C).[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Live Mode session error: {e}[/red]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FRIDAY Live Multimodal Vision Mode")
    parser.add_argument(
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        help="Pixels to stream from: screen, camera, none",
        choices=["camera", "screen", "none"],
    )
    args = parser.parse_args()
    run_live_mode(video_mode=args.mode)
