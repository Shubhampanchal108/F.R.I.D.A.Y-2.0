"""
=============================================================================
F.R.I.D.A.Y LIVE COMPUTER USE // KEYBOARD CONTROLLER
=============================================================================
Executes keystrokes, shortcuts, hotkeys, and text entry.
Includes automatic clipboard paste fallback for complex Unicode/multilingual text,
preventing character loss during UI input.
=============================================================================
"""

import time
import pyperclip
from typing import Dict, Any, List, Union
import pyautogui

from Live.computer_use.safety_guard import safety_guard


class KeyboardController:
    """
    Simulates physical keyboard interactions, hotkeys, and text inputs.
    """

    # Common valid Windows keyboard special keys
    VALID_KEYS = {
        "enter", "return", "tab", "space", "backspace", "delete", "esc", "escape",
        "up", "down", "left", "right", "home", "end", "pageup", "pagedown",
        "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
        "ctrl", "shift", "alt", "win", "windows", "capslock", "insert"
    }

    @staticmethod
    def _is_ascii(text: str) -> bool:
        """Checks if string consists purely of standard ASCII characters."""
        try:
            text.encode("ascii")
            return True
        except UnicodeEncodeError:
            return False

    def type_text(
        self,
        text: str,
        press_enter: bool = False,
        clear_first: bool = False,
        interval: float = 0.02
    ) -> Dict[str, Any]:
        """
        Types the specified string into the currently focused input field.

        Features:
        - If clear_first=True, sends Ctrl+A followed by Backspace to clean the field.
        - If text contains non-ASCII characters (e.g. Hindi, Unicode symbols, or special formatting),
          automatically leverages clipboard paste (Ctrl+V) to ensure 100% character fidelity.
        - If press_enter=True, hits Enter after entering text.
        """
        if safety_guard.is_stopped():
            return {"status": "error", "message": "Emergency stop is active."}

        try:
            # 1. Optionally clear existing input
            if clear_first:
                pyautogui.hotkey("ctrl", "a")
                time.sleep(0.04)
                pyautogui.press("backspace")
                time.sleep(0.05)

            # 2. Check if text requires clipboard paste (Unicode / non-ASCII)
            if not self._is_ascii(text) or len(text) > 200:
                # Save previous clipboard to restore later
                original_clip = ""
                try:
                    original_clip = pyperclip.paste()
                except Exception:
                    pass

                pyperclip.copy(text)
                time.sleep(0.05)
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.05)

                # Best-effort restore original clipboard
                try:
                    if original_clip and original_clip != text:
                        pyperclip.copy(original_clip)
                except Exception:
                    pass
            else:
                # Standard physical keystroke typing with slight interval
                pyautogui.write(text, interval=max(0.01, interval))

            # 3. Optionally submit
            if press_enter:
                time.sleep(0.05)
                pyautogui.press("enter")

            return {
                "status": "success",
                "action": "type_text",
                "length": len(text),
                "press_enter": press_enter,
                "cleared_first": clear_first
            }
        except pyautogui.FailSafeException:
            safety_guard.request_emergency_stop()
            return {"status": "aborted", "message": "PyAutoGUI FailSafe triggered during typing."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def press_key(self, key: str, count: int = 1, interval: float = 0.05) -> Dict[str, Any]:
        """
        Presses a single key (e.g., 'enter', 'tab', 'escape', 'down', 'f5').
        """
        if safety_guard.is_stopped():
            return {"status": "error", "message": "Emergency stop is active."}

        clean_key = key.lower().strip()
        if clean_key == "escape":
            clean_key = "esc"
        elif clean_key == "return":
            clean_key = "enter"

        try:
            for _ in range(max(1, count)):
                pyautogui.press(clean_key)
                if count > 1:
                    time.sleep(interval)

            return {
                "status": "success",
                "action": "press_key",
                "key": clean_key,
                "count": count
            }
        except pyautogui.FailSafeException:
            safety_guard.request_emergency_stop()
            return {"status": "aborted", "message": "PyAutoGUI FailSafe triggered."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def press_hotkey(self, combo: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Presses a combination of keys simultaneously (e.g., 'ctrl+c', 'alt+tab', 'ctrl+shift+i').
        """
        if safety_guard.is_stopped():
            return {"status": "error", "message": "Emergency stop is active."}

        if isinstance(combo, str):
            # Parse 'ctrl+shift+esc' or 'ctrl + c'
            parts = [p.strip().lower() for p in combo.replace("+", " ").split()]
        else:
            parts = [str(p).strip().lower() for p in combo]

        # Alias mappings
        normalized_parts = []
        for p in parts:
            if p in ["windows", "win"]:
                normalized_parts.append("win")
            elif p in ["escape"]:
                normalized_parts.append("esc")
            elif p in ["return"]:
                normalized_parts.append("enter")
            else:
                normalized_parts.append(p)

        try:
            pyautogui.hotkey(*normalized_parts)
            return {
                "status": "success",
                "action": "press_hotkey",
                "combination": "+".join(normalized_parts)
            }
        except pyautogui.FailSafeException:
            safety_guard.request_emergency_stop()
            return {"status": "aborted", "message": "PyAutoGUI FailSafe triggered during hotkey."}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Global Keyboard Controller Instance
keyboard_controller = KeyboardController()

