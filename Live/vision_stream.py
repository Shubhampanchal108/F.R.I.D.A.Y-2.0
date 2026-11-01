"""
=============================================================================
F.R.I.D.A.Y LIVE MULTIMODAL // REAL-TIME VISION STREAMER
=============================================================================
Streams real-time visual frames (desktop screen or webcam) to Google Gemini Live.
Includes frame rate pacing, dynamic resizing, and token-backlog prevention.
=============================================================================
"""

import io
import os
import sys
import threading
import asyncio
import cv2
import numpy as np
import PIL.Image
import mss
import pyautogui
from google.genai import types


class VisionStreamer:
    """
    High-performance real-time visual capture engine.
    Optimized for low bandwidth to prioritize real-time audio streams.
    Supports both desktop screen capture and webcam streaming.
    Includes visual coordinate grid overlay (0-1000 scale) for sub-pixel AI grounding.
    """

    def __init__(self, target_size=(768, 432), quality=60):
        self.target_size = target_size
        self.quality = quality
        self.cap = None
        self._cam_lock = threading.Lock()
        self.latest_camera_blob = None
        self._cached_grid = None
        self._cached_grid_dims = None

    def _get_grid_overlay(self, width: int, height: int) -> np.ndarray:
        """Precomputes and caches a high-contrast 0-1000 coordinate grid mask."""
        if self._cached_grid is not None and self._cached_grid_dims == (width, height):
            return self._cached_grid

        grid = np.zeros((height, width, 3), dtype=np.uint8)

        # 100-step grid lines (100, 200, 300, ... 900)
        for i in range(100, 1000, 100):
            gx = int(round((i / 1000.0) * width))
            gy = int(round((i / 1000.0) * height))

            # Subtle grid line
            cv2.line(grid, (gx, 0), (gx, height), (75, 75, 75), 1)
            cv2.line(grid, (0, gy), (width, gy), (75, 75, 75), 1)

            # High-visibility coordinate tick labels along top & left edges
            cv2.putText(grid, str(i), (gx + 3, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (230, 230, 230), 1, cv2.LINE_AA)
            cv2.putText(grid, str(i), (4, gy - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (230, 230, 230), 1, cv2.LINE_AA)

        # Center reference crosshair (500, 500)
        cx = int(round(0.5 * width))
        cy = int(round(0.5 * height))
        cv2.line(grid, (cx, 0), (cx, height), (0, 200, 255), 1)
        cv2.line(grid, (0, cy), (width, cy), (0, 200, 255), 1)
        cv2.putText(grid, "(500,500)", (cx + 5, cy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 255), 1, cv2.LINE_AA)

        self._cached_grid = grid
        self._cached_grid_dims = (width, height)
        return grid

    def _apply_grid_and_cursor(self, pil_img: PIL.Image.Image) -> PIL.Image.Image:
        """Overlays semi-transparent 0-1000 coordinate grid and mouse cursor target ring."""
        try:
            frame = np.array(pil_img)
            h, w = frame.shape[:2]
            grid = self._get_grid_overlay(w, h)

            # Fast Alpha blending: preserves crystal clear UI readability while keeping grid lines legible
            blended = cv2.addWeighted(frame, 0.88, grid, 0.42, 0)

            # Highlight physical mouse pointer with a high-visibility target ring and normalized coordinate badge
            try:
                cur_x, cur_y = pyautogui.position()
                cur_x = max(0, min(cur_x, w - 1))
                cur_y = max(0, min(cur_y, h - 1))
                norm_x = int(round((cur_x / max(1, w)) * 1000.0))
                norm_y = int(round((cur_y / max(1, h)) * 1000.0))

                # Outer neon target circle around cursor
                cv2.circle(blended, (cur_x, cur_y), 14, (0, 0, 255), 2, cv2.LINE_AA)
                cv2.circle(blended, (cur_x, cur_y), 3, (0, 255, 255), -1)

                badge = f"CURSOR: ({norm_x},{norm_y})"
                bx = min(w - 150, max(10, cur_x + 18))
                by = max(25, min(h - 10, cur_y + 5))
                cv2.putText(blended, badge, (bx, by), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 1, cv2.LINE_AA)
            except Exception:
                pass

            return PIL.Image.fromarray(blended)
        except Exception:
            return pil_img

    def _get_screen_blob(self):
        """Captures a screenshot of the primary monitor as a JPEG Blob."""
        img = None

        # 1. Try mss (fastest) with visible mouse cursor
        try:
            with mss.mss(with_cursor=True) as sct:
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
                with mss.mss(with_cursor=True) as sct:
                    monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                    shot = sct.grab(monitor)
                    img = PIL.Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
            except Exception:
                return None

        # 4. Apply semi-transparent 0-1000 coordinate grid & cursor position badge
        try:
            img = self._apply_grid_and_cursor(img)
        except Exception:
            pass

        try:
            # Preserve crisp high-definition resolution for desktop UI computer use
            if img.width > 1600:
                img.thumbnail((1600, 900))
            image_io = io.BytesIO()
            # Quality 80 ensures sharp button outlines and clear text readability
            img.save(image_io, format="JPEG", quality=80)
            return types.Blob(data=image_io.getvalue(), mime_type="image/jpeg")
        except Exception:
            return None

    def _open_camera_device(self):
        """Opens camera with DirectShow on Windows for instant initialization and warms up sensor."""
        c = None
        # Try DirectShow on Windows first for fast, reliable hardware initialization
        if sys.platform == "win32":
            try:
                for idx in [0, 1]:
                    test_cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                    if test_cap.isOpened():
                        c = test_cap
                        break
            except Exception:
                pass

        # Fallback to default backend
        if c is None or not c.isOpened():
            for idx in [0, 1]:
                test_cap = cv2.VideoCapture(idx)
                if test_cap.isOpened():
                    c = test_cap
                    break

        if c and c.isOpened():
            try:
                c.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                c.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                c.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            except Exception:
                pass
            # Warm up sensor so first frames are not pitch black
            for _ in range(4):
                c.read()
        return c

    def _capture_camera_frame(self):
        """Captures a frame from active webcam as a JPEG Blob."""
        with self._cam_lock:
            if not self.cap or not self.cap.isOpened():
                return None
            ret, frame = self.cap.read()
            if not ret or frame is None:
                return None
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = PIL.Image.fromarray(frame_rgb)
                img.thumbnail(self.target_size)
                image_io = io.BytesIO()
                img.save(image_io, format="JPEG", quality=self.quality)
                blob = types.Blob(data=image_io.getvalue(), mime_type="image/jpeg")
                self.latest_camera_blob = blob
                return blob
            except Exception:
                return None

    async def get_camera_blob(self):
        """Retrieves a fresh or latest camera frame blob to attach directly to user turns."""
        if self.cap and self.cap.isOpened():
            blob = await asyncio.to_thread(self._capture_camera_frame)
            if blob:
                return blob
        if self.latest_camera_blob:
            return self.latest_camera_blob

        # Standalone capture fallback if streaming loop is not running
        def _quick_capture():
            c = self._open_camera_device()
            if not c or not c.isOpened():
                return None
            ret, frame = c.read()
            c.release()
            if not ret or frame is None:
                return None
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = PIL.Image.fromarray(frame_rgb)
                img.thumbnail(self.target_size)
                image_io = io.BytesIO()
                img.save(image_io, format="JPEG", quality=self.quality)
                blob = types.Blob(data=image_io.getvalue(), mime_type="image/jpeg")
                self.latest_camera_blob = blob
                return blob
            except Exception:
                return None

        return await asyncio.to_thread(_quick_capture)

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
                await asyncio.sleep(0.5)

    async def stream_camera(self, session, send_lock, stop_event, interval=1.0):
        """Continuously captures and streams webcam frames."""
        self.cap = await asyncio.to_thread(self._open_camera_device)
        if not self.cap or not self.cap.isOpened():
            print("\n[VISION NOTICE]: Webcam could not be opened. Falling back to audio-only.\n", flush=True)
            return

        print("\n📷 [VISION STREAM]: Webcam streaming active.\n", flush=True)

        try:
            # Send initial webcam frame immediately
            init_blob = await asyncio.to_thread(self._capture_camera_frame)
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

                blob = await asyncio.to_thread(self._capture_camera_frame)
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
                    await asyncio.sleep(0.5)
        finally:
            with self._cam_lock:
                if self.cap:
                    self.cap.release()
                    self.cap = None
