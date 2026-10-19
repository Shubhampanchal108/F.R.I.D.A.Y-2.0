"""
=============================================================================
F.R.I.D.A.Y 2.0 // COMPUTER-USE & GUI AUTOMATION CONTROLLER
=============================================================================
Provides direct OS desktop control using normalized coordinates (0 to 1000).
Supports clicking, typing, hotkeys, scrolling, and dragging with PyAutoGUI.
=============================================================================
"""

import time
import pyautogui

# Safety Guardrails
pyautogui.FAILSAFE = True  # Move mouse to any corner to abort
pyautogui.PAUSE = 0.05


def _to_real_coords(norm_x: int, norm_y: int):
    """
    Converts normalized coordinates (0-1000 scale) to actual physical screen pixels.
    X: 0 = leftmost, 1000 = rightmost
    Y: 0 = topmost, 1000 = bottommost
    """
    screen_w, screen_h = pyautogui.size()
    # Clamp within 0-1000
    clamped_x = max(0, min(1000, int(norm_x)))
    clamped_y = max(0, min(1000, int(norm_y)))

    real_x = int((clamped_x / 1000.0) * screen_w)
    real_y = int((clamped_y / 1000.0) * screen_h)

    # Avoid exact (0,0) corner which triggers PyAutoGUI fail-safe
    real_x = max(2, min(screen_w - 3, real_x))
    real_y = max(2, min(screen_h - 3, real_y))
    return real_x, real_y, screen_w, screen_h


def click_screen(x: int, y: int, button: str = "left", clicks: int = 1):
    """
    Clicks on a visual element on the screen using normalized coordinates (0 to 1000).
    """
    try:
        rx, ry, sw, sh = _to_real_coords(x, y)
        pyautogui.moveTo(rx, ry, duration=0.2, tween=pyautogui.easeOutQuad)
        pyautogui.click(rx, ry, button=button, clicks=clicks)
        return {
            "status": "success",
            "action": "click_screen",
            "coords_norm": [x, y],
            "coords_pixels": [rx, ry],
            "screen_resolution": f"{sw}x{sh}",
            "button": button,
            "clicks": clicks,
        }
    except Exception as e:
        return {"status": "error", "action": "click_screen", "error": str(e)}


def double_click_screen(x: int, y: int):
    """
    Double clicks on an item on the screen (e.g. to open an app icon or select a word).
    """
    return click_screen(x, y, button="left", clicks=2)


def right_click_screen(x: int, y: int):
    """
    Right clicks on a visual element to open its context menu.
    """
    return click_screen(x, y, button="right", clicks=1)


def type_on_screen(text: str, press_enter: bool = False):
    """
    Types text into the currently active or focused input field.
    Optionally presses Enter key immediately after typing.
    """
    try:
        # Use clipboard paste for instant & unicode safe typing, or write directly
        import pyperclip
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.05)

        if press_enter:
            pyautogui.press("enter")

        return {
            "status": "success",
            "action": "type_on_screen",
            "text": text,
            "pressed_enter": press_enter,
        }
    except Exception:
        # Fallback to direct keyboard writing if pyperclip fails
        try:
            pyautogui.write(text, interval=0.02)
            if press_enter:
                pyautogui.press("enter")
            return {
                "status": "success",
                "action": "type_on_screen",
                "text": text,
                "pressed_enter": press_enter,
            }
        except Exception as e:
            return {"status": "error", "action": "type_on_screen", "error": str(e)}


def press_hotkey(keys: list):
    """
    Presses a combination of keys or a single key.
    Examples: ["ctrl", "t"] for new tab, ["alt", "f4"] to close, ["enter"], ["escape"].
    """
    try:
        if not keys:
            return {"status": "error", "action": "press_hotkey", "message": "No keys specified"}

        clean_keys = [str(k).lower().strip() for k in keys]
        pyautogui.hotkey(*clean_keys)
        return {
            "status": "success",
            "action": "press_hotkey",
            "keys": clean_keys,
        }
    except Exception as e:
        return {"status": "error", "action": "press_hotkey", "error": str(e)}


def scroll_screen(direction: str = "down", amount: int = 300):
    """
    Scrolls the active window up or down.
    direction: 'down' or 'up'
    amount: scrolling intensity (default 300)
    """
    try:
        scroll_amount = int(amount)
        if direction.lower() == "down":
            scroll_amount = -abs(scroll_amount)
        else:
            scroll_amount = abs(scroll_amount)

        pyautogui.scroll(scroll_amount)
        return {
            "status": "success",
            "action": "scroll_screen",
            "direction": direction,
            "amount": amount,
        }
    except Exception as e:
        return {"status": "error", "action": "scroll_screen", "error": str(e)}


def drag_and_drop_screen(start_x: int, start_y: int, end_x: int, end_y: int):
    """
    Drags from start coordinates to end coordinates using normalized (0-1000) scale.
    """
    try:
        sx, sy, _, _ = _to_real_coords(start_x, start_y)
        ex, ey, _, _ = _to_real_coords(end_x, end_y)

        pyautogui.moveTo(sx, sy, duration=0.2)
        pyautogui.dragTo(ex, ey, duration=0.5, button="left")
        return {
            "status": "success",
            "action": "drag_and_drop_screen",
            "from_pixels": [sx, sy],
            "to_pixels": [ex, ey],
        }
    except Exception as e:
        return {"status": "error", "action": "drag_and_drop_screen", "error": str(e)}


def move_cursor_to(x: int, y: int):
    """
    Smoothly moves the mouse cursor to the given normalized coordinates without clicking.
    """
    try:
        rx, ry, sw, sh = _to_real_coords(x, y)
        pyautogui.moveTo(rx, ry, duration=0.2, tween=pyautogui.easeOutQuad)
        return {
            "status": "success",
            "action": "move_cursor_to",
            "coords_pixels": [rx, ry],
        }
    except Exception as e:
        return {"status": "error", "action": "move_cursor_to", "error": str(e)}
