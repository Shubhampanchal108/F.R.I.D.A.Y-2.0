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
    Tracks cursor position history to enable instant undo/restore and fine micro-alignments.
    """

    def __init__(self, smooth_move: bool = True, default_duration: float = 0.2):
        self.smooth_move = smooth_move
        self.default_duration = default_duration
        self._cursor_history = []  # Stack of (px, py, timestamp)

    def _save_cursor_position(self):
        """Saves current cursor coordinates onto history stack before any movement."""
        try:
            cur_x, cur_y = pyautogui.position()
            if not self._cursor_history or self._cursor_history[-1][:2] != (cur_x, cur_y):
                self._cursor_history.append((cur_x, cur_y, time.time()))
                if len(self._cursor_history) > 30:
                    self._cursor_history.pop(0)
        except Exception:
            pass

    def restore_cursor(self) -> Dict[str, Any]:
        """
        Reverts the mouse cursor back to its previous original position before the last Friday action.
        """
        if safety_guard.is_stopped():
            return {"status": "error", "message": "Emergency stop is active."}

        if not self._cursor_history:
            return {"status": "error", "message": "No previous cursor position recorded in history."}

        cur_x, cur_y = pyautogui.position()
        orig_x, orig_y, _ = self._cursor_history.pop()

        # If current position matches popped top, pop one deeper to get the true previous spot
        if (cur_x, cur_y) == (orig_x, orig_y) and self._cursor_history:
            orig_x, orig_y, _ = self._cursor_history.pop()

        try:
            w, h = CoordinateMapper.get_screen_dimensions()
            orig_x, orig_y = safety_guard.validate_coordinates(orig_x, orig_y, w, h)
            pyautogui.moveTo(orig_x, orig_y, duration=0.2, tween=pyautogui.easeOutQuad)
            norm_x, norm_y = CoordinateMapper.pixel_to_normalized(orig_x, orig_y)
            return {
                "status": "success",
                "action": "restore_cursor",
                "restored_pixel": {"x": orig_x, "y": orig_y},
                "restored_normalized": {"norm_x": norm_x, "norm_y": norm_y},
                "message": f"Mouse cursor successfully restored to original position ({orig_x}, {orig_y})."
            }
        except pyautogui.FailSafeException:
            safety_guard.request_emergency_stop()
            return {"status": "aborted", "message": "PyAutoGUI FailSafe triggered."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def align_cursor(
        self,
        dx: float = 0,
        dy: float = 0,
        click_after: bool = False,
        button: str = "left",
        double_click: bool = False,
        element_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Nudges the mouse cursor by relative pixel offsets (dx, dy).
        dx: + right, - left. dy: + down, - up.
        If click_after=True, automatically clicks once aligned.
        """
        if safety_guard.is_stopped():
            return {"status": "error", "message": "Emergency stop is active."}

        try:
            self._save_cursor_position()
            cur_x, cur_y = pyautogui.position()
            w, h = CoordinateMapper.get_screen_dimensions()
            new_x = max(0, min(cur_x + int(round(dx)), w - 1))
            new_y = max(0, min(cur_y + int(round(dy)), h - 1))
            new_x, new_y = safety_guard.validate_coordinates(new_x, new_y, w, h)

            # Smoothly move to the aligned pixel position
            pyautogui.moveTo(new_x, new_y, duration=0.15, tween=pyautogui.easeOutQuad)
            norm_x, norm_y = CoordinateMapper.pixel_to_normalized(new_x, new_y)

            clicked = False
            if click_after:
                time.sleep(0.05)
                clicks = 2 if double_click else 1
                pyautogui.click(x=new_x, y=new_y, clicks=clicks, interval=0.08, button=button)
                clicked = True

            action_desc = f"{button}_click" if clicked else "align_cursor"
            return {
                "status": "success",
                "action": action_desc,
                "delta": {"dx": dx, "dy": dy},
                "new_pixel": {"x": new_x, "y": new_y},
                "new_normalized": {"norm_x": norm_x, "norm_y": norm_y},
                "clicked_after": clicked,
                "element_hint": element_hint,
                "message": (
                    f"Mouse cursor aligned by ({dx}, {dy}) to ({new_x}, {new_y})"
                    + (f" and {action_desc} executed." if clicked else ".")
                )
            }
        except pyautogui.FailSafeException:
            safety_guard.request_emergency_stop()
            return {"status": "aborted", "message": "PyAutoGUI FailSafe triggered."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

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

        # Save cursor position before moving so user or Friday can revert anytime
        self._save_cursor_position()

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
