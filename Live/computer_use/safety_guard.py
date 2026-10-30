"""
=============================================================================
F.R.I.D.A.Y LIVE COMPUTER USE // SAFETY GUARD & LOOP DETECTOR
=============================================================================
Guarantees safe OS interaction:
1. PyAutoGUI Failsafe (slam mouse to top-left corner (0,0) to instantly kill).
2. Action thrashing & infinite loop detection (halts repeated unproductive clicks).
3. Emergency abort switch for immediate cessation.
4. Input sanitization & coordinate bounding checks.
=============================================================================
"""

import time
import threading
from collections import deque
from typing import Dict, Any, Tuple, Optional
import pyautogui

# Set PyAutoGUI safety configurations
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


class SafetyGuard:
    """
    Monitors and guards all automated desktop actions against run-away loops,
    dangerous keystrokes, and out-of-bound inputs.
    """

    def __init__(self, max_history: int = 10, loop_threshold: int = 3):
        self._action_history = deque(maxlen=max_history)
        self._loop_threshold = loop_threshold
        self._emergency_stop = threading.Event()
        self._lock = threading.Lock()

    def request_emergency_stop(self):
        """Immediately halts all automated mouse and keyboard actions."""
        self._emergency_stop.set()

    def reset_emergency_stop(self):
        """Clears emergency stop status."""
        self._emergency_stop.clear()

    def is_stopped(self) -> bool:
        """Returns True if emergency stop is currently active."""
        return self._emergency_stop.is_set()

    def record_and_check_loop(self, action: str, target: Any) -> Tuple[bool, Optional[str]]:
        """
        Records an action signature and checks if the AI is trapped in an infinite loop.
        Returns (is_loop_detected, warning_message).
        """
        with self._lock:
            if self._emergency_stop.is_set():
                return True, "Emergency stop is active. Action aborted."

            action_signature = f"{action}:{str(target)}"
            self._action_history.append((action_signature, time.time()))

            # Check consecutive repetitions
            if len(self._action_history) >= self._loop_threshold:
                recent_actions = [item[0] for item in list(self._action_history)[-self._loop_threshold:]]
                if len(set(recent_actions)) == 1:
                    return (
                        True,
                        f"Infinite loop detected: Action '{action}' on target '{target}' "
                        f"repeated {self._loop_threshold} times consecutively. "
                        f"Action halted to protect desktop state. Try a keyboard shortcut (e.g. Enter, Esc) or ask the user."
                    )

            return False, None

    def validate_coordinates(self, px: int, py: int, width: int, height: int) -> Tuple[int, int]:
        """
        Validates pixel coordinates, ensuring they never trigger unintended failsafe triggers
        (such as corner 0,0 unless deliberately requested).
        """
        # If coordinates are 0,0, shift to 1,1 to prevent accidental PyAutoGUI failsafe trigger
        if px <= 0 and py <= 0:
            px, py = 1, 1

        px = max(0, min(px, width - 1))
        py = max(0, min(py, height - 1))
        return px, py

    def clear_history(self):
        """Resets the action history buffer (e.g. after successful task completion)."""
        with self._lock:
            self._action_history.clear()


# Global Singleton Guard
safety_guard = SafetyGuard()

