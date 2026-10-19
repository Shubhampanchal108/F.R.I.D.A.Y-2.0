"""
=============================================================================
F.R.I.D.A.Y LIVE MULTIMODAL // BIDIRECTIONAL AUDIO ENGINE
=============================================================================
Handles real-time microphone input sampling and neural speaker playback.
Includes hardware buffer overflow management and echo cancellation.
=============================================================================
"""

import asyncio
import pyaudio
from google.genai import types

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024


class AudioStreamer:
    """
    Manages low-latency duplex audio streaming for Gemini Live.
    """

    def __init__(self):
        self.pya = pyaudio.PyAudio()
        self.audio_in_queue = asyncio.Queue()
        self.audio_stream = None
        self.output_stream = None
        self.is_playing = asyncio.Event()

    async def start_mic_stream(self):
        """Initializes hardware microphone stream."""
        try:
            mic_info = self.pya.get_default_input_device_info()
            self.audio_stream = await asyncio.to_thread(
                self.pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=SEND_SAMPLE_RATE,
                input=True,
                input_device_index=mic_info["index"],
                frames_per_buffer=CHUNK_SIZE,
            )
            return True
        except Exception as e:
            print(f"\n[AUDIO WARNING]: Microphone initialization error: {e}\n", flush=True)
            return False

    async def start_speaker_stream(self):
        """Initializes hardware speaker output stream."""
        try:
            self.output_stream = await asyncio.to_thread(
                self.pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
            )
            return True
        except Exception as e:
            print(f"\n[AUDIO WARNING]: Speaker output initialization error: {e}\n", flush=True)
            return False

    async def listen_audio_loop(self, session, send_lock, stop_event):
        """
        Continuously reads PCM audio from hardware microphone and streams to Gemini Live.
        Enables Gemini Live's real-time Voice Activity Detection (VAD) and user interruption.
        """
        if not self.audio_stream:
            ok = await self.start_mic_stream()
            if not ok:
                print("\n[bold red]❌ Failed to initialize microphone stream.[/bold red]\n", flush=True)
                return

        print("🎙️ [AUDIO STREAM]: Hardware microphone active and streaming live audio (16000Hz Mono PCM)...", flush=True)

        kwargs = {"exception_on_overflow": False}
        while not stop_event.is_set():
            try:
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
                if not data:
                    await asyncio.sleep(0.01)
                    continue

                # Echo Gate: If Friday is speaking via speakers, suppress mic forwarding to prevent acoustic feedback loop
                if self.is_playing.is_set():
                    await asyncio.sleep(0.01)
                    continue

                blob = types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                async with send_lock:
                    await session.send_realtime_input(audio=blob)

            except Exception as e:
                if not stop_event.is_set():
                    print(f"\n[MIC STREAM NOTICE]: {e}\n", flush=True)
                    await asyncio.sleep(0.02)
                else:
                    break

    async def play_audio_loop(self, stop_event):
        """
        Continuously dequeues neural audio PCM chunks received from Gemini Live
        and writes them to the speaker output.
        """
        if not self.output_stream:
            ok = await self.start_speaker_stream()
            if not ok:
                return

        while not stop_event.is_set():
            try:
                bytestream = await asyncio.wait_for(self.audio_in_queue.get(), timeout=0.2)
                self.is_playing.set()
                await asyncio.to_thread(self.output_stream.write, bytestream)
                if self.audio_in_queue.empty():
                    # Grace period to allow speaker acoustic reverb to decay
                    await asyncio.sleep(0.12)
                    self.is_playing.clear()
            except asyncio.TimeoutError:
                self.is_playing.clear()
                continue
            except Exception:
                self.is_playing.clear()
                if stop_event.is_set():
                    break

    def close(self):
        """Closes all hardware audio streams."""
        self.is_playing.clear()
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except Exception:
                pass
            self.audio_stream = None

        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
            except Exception:
                pass
            self.output_stream = None

        try:
            self.pya.terminate()
        except Exception:
            pass
