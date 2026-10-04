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

from google import genai
from google.genai import types
from dotenv import dotenv_values
from rich.console import Console
from rich.panel import Panel
from rich import box

# Parent directory for relative imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from configs import Friday_Instruction as Friday_Details
except Exception:
    Friday_Details = (
        "You are F.R.I.D.A.Y (Friendly Reliable Intelligent Digital Assistant for Youth), created by Shubham sir. "
        "You are currently operating in LIVE MULTIMODAL STREAMING MODE. "
        "You can continuously see real-time visual frames (from the desktop screen or camera) and hear real-time audio from the user. "
        "Rules: "
        "1. Always address the user politely as 'Sir' or 'Shubham sir'. "
        "2. If asked about what is on screen or in front of the camera, describe it accurately, pointing out code, UI elements, errors, or objects. "
        "3. Keep spoken replies concise, natural, and conversational (around 1-3 sentences unless explaining a complex problem). "
        "4. Support both English and natural Hindi (Hinglish) based on user query. "
        "5. Do NOT output raw JSON or code tags in spoken audio."
    )

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 800

MODEL = "models/gemini-2.5-flash-native-audio-preview-09-2025"
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
        self.out_queue = None
        self.session = None
        self.audio_stream = None
        self.output_stream = None

        # Flags for playback and termination
        self.is_playing = asyncio.Event()
        self.stop_event = asyncio.Event()

    async def send_text(self):
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
        img.thumbnail([1024, 1024])

        image_io = io.BytesIO()
        img.save(image_io, format="JPEG", quality=75)
        return types.Blob(data=image_io.getvalue(), mime_type="image/jpeg")

    async def get_frames(self):
        cap = await asyncio.to_thread(cv2.VideoCapture, 0)
        if not cap.isOpened():
            console.print("\n[bold red]⚠️ Webcam could not be opened on device 0. Audio-only mode active.[/bold red]")
            return

        try:
            while not self.stop_event.is_set():
                blob = await asyncio.to_thread(self._get_frame, cap)
                if blob is None:
                    await asyncio.sleep(0.5)
                    continue
                await asyncio.sleep(1.0)
                try:
                    await self.out_queue.put(blob)
                except Exception:
                    break
        finally:
            cap.release()

    def _get_screen(self):
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                i = sct.grab(monitor)

                img = PIL.Image.frombytes("RGB", i.size, i.rgb)
                img.thumbnail([1024, 1024])

                image_io = io.BytesIO()
                img.save(image_io, format="JPEG", quality=70)
                return types.Blob(data=image_io.getvalue(), mime_type="image/jpeg")
        except Exception:
            return None

    async def get_screen(self):
        while not self.stop_event.is_set():
            blob = await asyncio.to_thread(self._get_screen)
            if blob is None:
                await asyncio.sleep(1.0)
                continue
            await asyncio.sleep(1.0)
            try:
                await self.out_queue.put(blob)
            except Exception:
                break

    async def send_realtime(self):
        while not self.stop_event.is_set():
            try:
                blob = await asyncio.wait_for(self.out_queue.get(), timeout=0.2)
                await self.session.send_realtime_input(media=blob)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if self.stop_event.is_set():
                    break
                await asyncio.sleep(0.05)

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

        kwargs = {"exception_on_overflow": False} if __debug__ else {}
        while not self.stop_event.is_set():
            if self.is_playing.is_set():
                await asyncio.sleep(0.05)
                continue

            try:
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
                blob = types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                await self.out_queue.put(blob)
            except Exception:
                if self.stop_event.is_set():
                    break
                await asyncio.sleep(0.05)

    async def receive_audio(self):
        new_turn = True
        try:
            while not self.stop_event.is_set():
                turn = self.session.receive()
                async for response in turn:
                    if self.stop_event.is_set():
                        break
                    if data := response.data:
                        self.audio_in_queue.put_nowait(data)
                    if text := response.text:
                        if new_turn:
                            console.print("\n[bold cyan]🤖 F.R.I.D.A.Y:[/bold cyan] ", end="", highlight=False)
                            new_turn = False
                        print(text, end="", flush=True)

                new_turn = True
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

        try:
            async with (
                client.aio.live.connect(model=MODEL, config=config) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=10)

                send_text_task = tg.create_task(self.send_text())
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())

                if self.video_mode == "camera":
                    tg.create_task(self.get_frames())
                elif self.video_mode == "screen":
                    tg.create_task(self.get_screen())

                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                await send_text_task
                self.stop_event.set()
                raise asyncio.CancelledError("User requested exit")

        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        except ExceptionGroup as eg:
            for exc in eg.exceptions:
                if not isinstance(exc, (asyncio.CancelledError, KeyboardInterrupt)):
                    console.print(f"\n[bold red]⚠️ Notice: {exc}[/bold red]")
        except Exception as e:
            console.print(f"\n[bold red]⚠️ Live Mode Notice: {e}[/bold red]")
        finally:
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
        f"[bold white]Gemini Model:[/bold white] [dim]{MODEL}[/dim]\n\n"
        f"[bold yellow]Instructions:[/bold yellow]\n"
        f" • Speak directly into your microphone to talk to FRIDAY.\n"
        f" • Friday can see your {'screen in real time' if video_mode == 'screen' else 'webcam in real time'}.\n"
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
