"""
=============================================================================
F.R.I.D.A.Y LIVE MULTIMODAL // COMPUTER USE PACKAGE
=============================================================================
Autonomous Visual Computer Use Agent for Live Screen Mode.
Provides closed-loop UI perception, human-like mouse/keyboard control,
coordinate resolution, and anti-thrashing safety guards.
=============================================================================
"""

from Live.computer_use.coordinate_mapper import CoordinateMapper
from Live.computer_use.safety_guard import safety_guard, SafetyGuard
from Live.computer_use.mouse_controller import mouse_controller, MouseController
from Live.computer_use.keyboard_controller import keyboard_controller, KeyboardController
from Live.computer_use.screen_verifier import screen_verifier, ScreenVerifier
from Live.computer_use.actions import (
    execute_computer_action,
    COMPUTER_ACTIONS,
    computer_click,
    computer_type,
    computer_press_key,
    computer_scroll,
    computer_drag,
    computer_inspect_screen,
    computer_reset_safety,
)
from Live.computer_use.schemas import COMPUTER_USE_SCHEMAS


def is_computer_use_tool(tool_name: str) -> bool:
    """
    Returns True if tool_name belongs to the Live Computer Use system.
    """
    return tool_name in COMPUTER_ACTIONS


__all__ = [
    "CoordinateMapper",
    "safety_guard",
    "SafetyGuard",
    "mouse_controller",
    "MouseController",
    "keyboard_controller",
    "KeyboardController",
    "screen_verifier",
    "ScreenVerifier",
    "execute_computer_action",
    "is_computer_use_tool",
    "COMPUTER_ACTIONS",
    "COMPUTER_USE_SCHEMAS",
    "computer_click",
    "computer_type",
    "computer_press_key",
    "computer_scroll",
    "computer_drag",
    "computer_inspect_screen",
    "computer_reset_safety",
]

