"""
=============================================================================
F.R.I.D.A.Y LIVE MULTIMODAL // REAL-TIME VISION STREAMER
=============================================================================
Streams real-time visual frames (desktop screen or webcam) to Google Gemini Live.
Includes frame rate pacing, dynamic resizing, and token-backlog prevention.
=============================================================================
"""

import io
import asyncio
import cv2
import PIL.Image
import mss
from google.genai import types


class VisionStreamer:
    """
    High-performance real-time visual capture engine.
    Optimized for low bandwidth to prioritize real-time audio streams.
    """

    def __init__(self, target_size=(768, 432), quality=45):
        self.target_size = target_size
        self.quality = quality

    def _get_screen_blob(self):
        """Captures a screenshot of the primary monitor as a JPEG Blob."""
        img = None

        # 1. Try mss (fastest)
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                shot = sct.grab(monitor)
                pil_img = PIL.Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
                extrema = pil_img.getextrema()
                if extrema != ((0, 0), (0, 0), (0, 0)):
                    img = pil_img
        except Exception:
            pass

        # 2. Try PIL ImageGrab fallback
        if img is None:
            try:
                import PIL.ImageGrab
                pil_img = PIL.ImageGrab.grab()
                if pil_img and pil_img.getextrema() != ((0, 0), (0, 0), (0, 0)):
                    img = pil_img
            except Exception:
                pass

        # 3. Fallback to shot if both were dark (e.g. dark desktop theme)
        if img is None:
            try:
                with mss.mss() as sct:
                    monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                    shot = sct.grab(monitor)
                    img = PIL.Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
            except Exception:
                return None

        try:
            img.thumbnail(self.target_size)
            image_io = io.BytesIO()
            img.save(image_io, format="JPEG", quality=self.quality)
            return types.Blob(data=image_io.getvalue(), mime_type="image/jpeg")
        except Exception:
            return None

    def _get_camera_blob(self, cap):
        """Captures a frame from the webcam VideoCapture as a JPEG Blob."""
        ret, frame = cap.read()
        if not ret or frame is None:
            return None
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)
        img.thumbnail(self.target_size)
        image_io = io.BytesIO()
        img.save(image_io, format="JPEG", quality=self.quality)
        return types.Blob(data=image_io.getvalue(), mime_type="image/jpeg")

    async def stream_screen(self, session, send_lock, stop_event, interval=1.5):
        """Continuously captures and streams desktop screen frames."""
        # Send initial screen frame immediately
        init_blob = await asyncio.to_thread(self._get_screen_blob)
        if init_blob:
            try:
                async with send_lock:
                    await session.send_realtime_input(media=init_blob)
            except Exception as e:
                err_msg = str(e).lower()
                if "closed" in err_msg or "no close frame" in err_msg or "1006" in err_msg:
                    stop_event.set()
                    return

        while not stop_event.is_set():
            await asyncio.sleep(interval)
            if stop_event.is_set():
                break

            blob = await asyncio.to_thread(self._get_screen_blob)
            if blob is None:
                continue

            try:
                async with send_lock:
                    await session.send_realtime_input(media=blob)
            except Exception as e:
                err_msg = str(e).lower()
                if "closed" in err_msg or "no close frame" in err_msg or "1006" in err_msg:
                    stop_event.set()
                break

    async def stream_camera(self, session, send_lock, stop_event, interval=1.0):
        """Continuously captures and streams webcam frames."""
        cap = await asyncio.to_thread(cv2.VideoCapture, 0)
        if not cap.isOpened():
            print("\n[VISION NOTICE]: Webcam could not be opened on device 0. Falling back to audio-only.\n", flush=True)
            return

        try:
            # Send initial webcam frame immediately
            init_blob = await asyncio.to_thread(self._get_camera_blob, cap)
            if init_blob:
                try:
                    async with send_lock:
                        await session.send_realtime_input(media=init_blob)
                except Exception:
                    pass

            while not stop_event.is_set():
                await asyncio.sleep(interval)
                if stop_event.is_set():
                    break

                blob = await asyncio.to_thread(self._get_camera_blob, cap)
                if blob is None:
                    continue

                try:
                    async with send_lock:
                        await session.send_realtime_input(media=blob)
                except Exception:
                    if stop_event.is_set():
                        break
        finally:
            cap.release()
