"""
=============================================================================
F.R.I.D.A.Y LIVE COMPUTER USE // MOUSE CONTROLLER
=============================================================================
Executes human-like cursor movements, clicks, double-clicks, contextual menus,
drag-and-drop gestures, and vertical/horizontal scrolling with sub-pixel safety.
=============================================================================
"""

import time
import math
from typing import Dict, Any, Optional
import pyautogui

from Live.computer_use.coordinate_mapper import CoordinateMapper
from Live.computer_use.safety_guard import safety_guard


class MouseController:
    """
    Simulates physical mouse interactions on the desktop interface.
    """

    def __init__(self, smooth_move: bool = True, default_duration: float = 0.2):
        self.smooth_move = smooth_move
        self.default_duration = default_duration

    def move_to(
        self,
        norm_x: float,
        norm_y: float,
        element_hint: Optional[str] = None,
        duration: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Moves the mouse cursor to target coordinates with landmark snapping.
        """
        if safety_guard.is_stopped():
            return {"status": "error", "message": "Emergency stop is active."}

        px, py = CoordinateMapper.resolve_target_pixel(norm_x, norm_y, element_hint=element_hint)
        w, h = CoordinateMapper.get_screen_dimensions()
        px, py = safety_guard.validate_coordinates(px, py, w, h)

        dur = self.default_duration if duration is None else duration
        try:
            if self.smooth_move and dur > 0:
                pyautogui.moveTo(px, py, duration=dur, tween=pyautogui.easeOutQuad)
            else:
                pyautogui.moveTo(px, py)

            return {
                "status": "success",
                "action": "move_to",
                "normalized": {"x": norm_x, "y": norm_y},
                "pixel": {"x": px, "y": py},
                "element_hint": element_hint
            }
        except pyautogui.FailSafeException:
            safety_guard.request_emergency_stop()
            return {"status": "aborted", "message": "PyAutoGUI FailSafe triggered by user cursor override."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def click(
        self,
        norm_x: float,
        norm_y: float,
        button: str = "left",
        clicks: int = 1,
        interval: float = 0.1,
        element_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Performs single, double, or triple clicks at normalized coordinates.
        Supports 'left', 'right', 'middle' buttons.
        """
        # Check loop thrashing
        is_loop, warning = safety_guard.record_and_check_loop(f"click_{button}_{clicks}", (norm_x, norm_y))
        if is_loop:
            return {"status": "blocked", "message": warning}

        # Move to coordinate with landmark snapping
        move_res = self.move_to(norm_x, norm_y, element_hint=element_hint)
        if move_res.get("status") != "success":
            return move_res

        px, py = move_res["pixel"]["x"], move_res["pixel"]["y"]

        try:
            time.sleep(0.06)  # Settle pause for UI responsiveness
            pyautogui.click(x=px, y=py, clicks=clicks, interval=interval, button=button)

            return {
                "status": "success",
                "action": f"{button}_click",
                "clicks": clicks,
                "coordinates": {"norm_x": norm_x, "norm_y": norm_y, "px": px, "py": py},
                "element_hint": element_hint
            }
        except pyautogui.FailSafeException:
            safety_guard.request_emergency_stop()
            return {"status": "aborted", "message": "PyAutoGUI FailSafe triggered."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def double_click(
        self,
        norm_x: float,
        norm_y: float,
        button: str = "left",
        element_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Performs a rapid double-click."""
        return self.click(norm_x, norm_y, button=button, clicks=2, interval=0.08, element_hint=element_hint)

    def right_click(
        self,
        norm_x: float,
        norm_y: float,
        element_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Performs a right-click to summon context menus."""
        return self.click(norm_x, norm_y, button="right", clicks=1, element_hint=element_hint)

    def drag_to(
        self,
        from_norm_x: float,
        from_norm_y: float,
        to_norm_x: float,
        to_norm_y: float,
        button: str = "left",
        duration: float = 0.5
    ) -> Dict[str, Any]:
        """Drags an element from start coordinates to destination coordinates."""
        if safety_guard.is_stopped():
            return {"status": "error", "message": "Emergency stop is active."}

        from_px, from_py = CoordinateMapper.resolve_target_pixel(from_norm_x, from_norm_y)
        to_px, to_py = CoordinateMapper.resolve_target_pixel(to_norm_x, to_norm_y)
        w, h = CoordinateMapper.get_screen_dimensions()
        from_px, from_py = safety_guard.validate_coordinates(from_px, from_py, w, h)
        to_px, to_py = safety_guard.validate_coordinates(to_px, to_py, w, h)

        try:
            pyautogui.moveTo(from_px, from_py, duration=0.15)
            pyautogui.mouseDown(button=button)
            time.sleep(0.08)

            pyautogui.moveTo(to_px, to_py, duration=max(0.3, duration), tween=pyautogui.easeInOutQuad)
            time.sleep(0.08)
            pyautogui.mouseUp(button=button)

            return {
                "status": "success",
                "action": "drag_to",
                "from": {"norm_x": from_norm_x, "norm_y": from_norm_y, "px": from_px, "py": from_py},
                "to": {"norm_x": to_norm_x, "norm_y": to_norm_y, "px": to_px, "py": to_py}
            }
        except pyautogui.FailSafeException:
            safety_guard.request_emergency_stop()
            return {"status": "aborted", "message": "PyAutoGUI FailSafe triggered during drag."}
        except Exception as e:
            try:
                pyautogui.mouseUp(button=button)
            except Exception:
                pass
            return {"status": "error", "message": str(e)}

    def scroll(
        self,
        direction: str = "down",
        amount: int = 5,
        norm_x: Optional[float] = None,
        norm_y: Optional[float] = None
    ) -> Dict[str, Any]:
        """Performs vertical scrolling."""
        if safety_guard.is_stopped():
            return {"status": "error", "message": "Emergency stop is active."}

        if norm_x is not None and norm_y is not None:
            self.move_to(norm_x, norm_y, duration=0.1)

        ticks = max(1, int(amount)) * 120
        scroll_amount = -ticks if direction.lower() == "down" else ticks

        try:
            pyautogui.scroll(scroll_amount)
            return {
                "status": "success",
                "action": "scroll",
                "direction": direction,
                "amount": amount,
                "scroll_ticks": scroll_amount
            }
        except pyautogui.FailSafeException:
            safety_guard.request_emergency_stop()
            return {"status": "aborted", "message": "PyAutoGUI FailSafe triggered during scroll."}
        except Exception as e:
            return {"status": "error", "message": str(e)}


mouse_controller = MouseController()
