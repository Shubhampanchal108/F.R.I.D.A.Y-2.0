"""
=============================================================================
F.R.I.D.A.Y LIVE COMPUTER USE // COORDINATE MAPPER
=============================================================================
Handles display resolution detection, DPI awareness, coordinate scaling,
and intelligent Windows UI landmark snapping for sub-pixel click accuracy.
=============================================================================
"""

import sys
import ctypes
from typing import Tuple, Dict, Any, Optional
import pyautogui

_dpi_initialized = False

def _ensure_dpi_aware():
    global _dpi_initialized
    if _dpi_initialized:
        return
    _dpi_initialized = True
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


class CoordinateMapper:
    """
    Translates normalized coordinates (0-1000 grid) or direct pixels from vision models
    into precise physical desktop screen pixel positions, with UI Landmark Snapping.
    """

    @staticmethod
    def get_screen_dimensions() -> Tuple[int, int]:
        """
        Returns (screen_width, screen_height) of primary desktop display.
        """
        _ensure_dpi_aware()
        size = pyautogui.size()
        return int(size.width), int(size.height)

    @classmethod
    def resolve_target_pixel(
        cls,
        x: float,
        y: float,
        element_hint: Optional[str] = None
    ) -> Tuple[int, int]:
        """
        Resolves input coordinates into physical screen pixels with high precision.
        Handles:
        1. Float normalized: [0.0, 1.0]
        2. Integer normalized: [0, 1000]
        3. Raw screen pixels: (> 1000 or explicit pixel ranges)
        4. Smart Windows UI Landmark Snapping for common controls.
        """
        width, height = cls.get_screen_dimensions()

        # Case 1: Raw screen pixels already
        if x > 1000 or y > 1000:
            px = int(round(x))
            py = int(round(y))
        # Case 2: Float normalized [0.0, 1.0]
        elif 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and (x > 0 or y > 0):
            px = int(round(x * width))
            py = int(round(y * height))
        # Case 3: Normalized 0-1000 grid
        else:
            px = int(round((x / 1000.0) * width))
            py = int(round((y / 1000.0) * height))

        # Clamp safely within screen boundaries
        px = max(0, min(px, width - 1))
        py = max(0, min(py, height - 1))

        # ---- SMART UI LANDMARK SNAPPING ----
        if element_hint:
            hint = str(element_hint).lower().strip()

            # 1. Windows Window Controls (top-right of active/maximized window)
            if any(k in hint for k in ["close", "exit", "quit", "band karo"]):
                if px > width * 0.85 and py < height * 0.15:
                    px, py = width - 22, 16  # Center of [X] close button
            elif any(k in hint for k in ["maximize", "bada karo", "fullscreen"]):
                if px > width * 0.80 and py < height * 0.15:
                    px, py = width - 68, 16  # Center of [square] maximize button
            elif any(k in hint for k in ["minimize", "chota karo", "hide"]):
                if px > width * 0.75 and py < height * 0.15:
                    px, py = width - 110, 16 # Center of [-] minimize button

            # 2. Windows Taskbar & Start Menu
            elif any(k in hint for k in ["start", "start menu", "windows menu"]):
                if py > height * 0.85:
                    px, py = 24, height - 20 # Center of Windows Start icon

            # 3. Web Browser URL / Search Bar
            elif any(k in hint for k in ["url", "address", "search bar", "address bar"]):
                if py < height * 0.22:
                    py = 78  # Exact vertical center of standard Chrome/Edge URL bar
                    px = max(int(width * 0.25), min(px, int(width * 0.75)))

            # 4. Web Browser New Tab (+) Button
            elif any(k in hint for k in ["new tab", "naya tab", "add tab"]):
                if py < height * 0.12:
                    py = 24  # Standard browser tab strip vertical center

        return px, py

    @classmethod
    def normalized_to_pixel(cls, norm_x: float, norm_y: float) -> Tuple[int, int]:
        """Backward compatible normalized 0-1000 mapper."""
        return cls.resolve_target_pixel(norm_x, norm_y)

    @classmethod
    def pixel_to_normalized(cls, px: int, py: int) -> Tuple[int, int]:
        """Converts pixel coordinates to normalized 0-1000 integer grid."""
        width, height = cls.get_screen_dimensions()
        norm_x = int(round((px / max(1, width)) * 1000.0))
        norm_y = int(round((py / max(1, height)) * 1000.0))
        return max(0, min(norm_x, 1000)), max(0, min(norm_y, 1000))

    @classmethod
    def get_display_info(cls) -> Dict[str, Any]:
        """Returns diagnostic information about current screen setup."""
        w, h = cls.get_screen_dimensions()
        cur_x, cur_y = pyautogui.position()
        norm_cx, norm_cy = cls.pixel_to_normalized(cur_x, cur_y)

        return {
            "screen_width": w,
            "screen_height": h,
            "cursor_pixel": {"x": cur_x, "y": cur_y},
            "cursor_normalized": {"norm_x": norm_cx, "norm_y": norm_cy},
            "aspect_ratio": f"{round(w / max(1, h), 2)}:1",
        }
