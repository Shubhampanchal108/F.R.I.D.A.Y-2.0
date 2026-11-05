"""
=============================================================================
F.R.I.D.A.Y LIVE MULTIMODAL // BIDIRECTIONAL AUDIO ENGINE
=============================================================================
Handles real-time continuous microphone input sampling and neural speaker playback.
Optimized for ZERO LATENCY: keeps hardware mic stream open persistently without
restarting devices, and uses active buffer draining to eliminate acoustic feedback.
=============================================================================
"""

import time
import asyncio
import pyaudio
import numpy as np
from google.genai import types

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024


class AudioStreamer:
    """
    Manages ultra-low-latency persistent duplex audio streaming for Gemini Live.
    """

    def __init__(self):
        self.pya = pyaudio.PyAudio()
        self.audio_in_queue = asyncio.Queue()
        self.audio_stream = None
        self.output_stream = None
        self.is_playing = asyncio.Event()
        self.last_audio_playback_time: float = 0.0

    def is_speaker_busy(self, cooldown_seconds: float = 0.25) -> bool:
        """
        Returns True if the speaker is actively outputting sound or within
        a brief 250ms hardware reverb decay window.
        """
        if self.is_playing.is_set():
            return True
        if (time.time() - self.last_audio_playback_time) < cooldown_seconds:
            return True
        return False

    async def start_mic_stream(self):
        """Initializes hardware microphone stream once and keeps it persistently open."""
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
        Continuously reads PCM audio from the persistent hardware microphone.
        - Streams in real-time at 16000Hz PCM directly to Gemini Live WebSocket.
        - When Friday speaks: continuously reads & drains hardware buffer (so speaker audio
          is dumped and never queued) without closing/reopening the mic stream.
        - As soon as Friday finishes speaking: user voice flows instantly with 0ms delay.
        """
        if not self.audio_stream:
            ok = await self.start_mic_stream()
            if not ok:
                print("\n[bold red]❌ Failed to initialize microphone stream.[/bold red]\n", flush=True)
                return

        print("🎙️ [AUDIO STREAM]: Persistent hardware microphone active (Zero-Latency Real-Time Audio)...", flush=True)

        kwargs = {"exception_on_overflow": False}

        while not stop_event.is_set():
            try:
                # 1. Read hardware microphone buffer continuously in worker thread
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
                if not data:
                    await asyncio.sleep(0.005)
                    continue

                # 2. While Friday is speaking or in brief 250ms reverb cooldown:
                # DRAIN BUFFER AND DISCARD so no speaker audio leaks into the session!
                if self.is_speaker_busy(cooldown_seconds=0.25):
                    continue

                # 3. Calculate sound energy to filter background static/hiss
                samples = np.frombuffer(data, dtype=np.int16)
                rms = float(np.sqrt(np.mean(samples.astype(np.float32)**2))) if len(samples) > 0 else 0.0

                if rms < 100.0:
                    continue

                # 4. Stream directly to Gemini Live WebSocket with zero delay
                blob = types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                async with send_lock:
                    await session.send_realtime_input(audio=blob)

            except Exception as e:
                err_msg = str(e).lower()
                if "closed" in err_msg or "no close frame" in err_msg or "1006" in err_msg:
                    stop_event.set()
                    break
                if not stop_event.is_set():
                    await asyncio.sleep(0.05)
                else:
                    break

    def clear_playback(self):
        """Instantly clears audio output queue on barge-in / user interruption."""
        self.is_playing.clear()
        self.last_audio_playback_time = time.time()
        while not self.audio_in_queue.empty():
            try:
                self.audio_in_queue.get_nowait()
            except Exception:
                break

    async def play_audio_loop(self, stop_event):
        """
        Continuously dequeues neural audio PCM chunks received from Gemini Live
        and writes them to the speaker output with timestamp tracking.
        """
        if not self.output_stream:
            ok = await self.start_speaker_stream()
            if not ok:
                return

        while not stop_event.is_set():
            try:
                bytestream = await asyncio.wait_for(self.audio_in_queue.get(), timeout=0.15)
                self.is_playing.set()
                self.last_audio_playback_time = time.time()
                await asyncio.to_thread(self.output_stream.write, bytestream)
                self.last_audio_playback_time = time.time()

                if self.audio_in_queue.empty():
                    await asyncio.sleep(0.15)
                    if self.audio_in_queue.empty():
                        self.is_playing.clear()
            except asyncio.TimeoutError:
                if self.audio_in_queue.empty():
                    self.is_playing.clear()
                continue
            except Exception:
                self.is_playing.clear()
                if stop_event.is_set():
                    break

    def close(self):
        """Closes all hardware audio streams upon session exit."""
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
