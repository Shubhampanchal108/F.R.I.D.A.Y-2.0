"""
=============================================================================
F.R.I.D.A.Y LIVE COMPUTER USE // ACTION DISPATCHER & RUNNER
=============================================================================
High-level operational facade for multimodal computer control:
- Resolves normalized coordinates & UI landmark snapping
- Real-time terminal diagnostic logging of mapped pixels
- Enforces closed-loop visual verification
- Dispatches click, type, hotkey, scroll, and drag actions
=============================================================================
"""

import time
from typing import Dict, Any, Optional
from rich.console import Console

from Live.computer_use.coordinate_mapper import CoordinateMapper
from Live.computer_use.safety_guard import safety_guard
from Live.computer_use.mouse_controller import mouse_controller
from Live.computer_use.keyboard_controller import keyboard_controller
from Live.computer_use.screen_verifier import screen_verifier

console = Console()


def computer_click(
    x: float,
    y: float,
    button: str = "left",
    double_click: bool = False,
    element_hint: Optional[str] = None,
    verify: bool = True
) -> Dict[str, Any]:
    """
    Clicks on the desktop at normalized coordinates (0-1000) with closed-loop visual verification
    and intelligent UI landmark snapping.
    """
    w, h = CoordinateMapper.get_screen_dimensions()
    target_px, target_py = CoordinateMapper.resolve_target_pixel(x, y, element_hint=element_hint)

    # Real-time console diagnostics so user and developer see exactly where Friday aims
    label = f"[bold yellow]'{element_hint}'[/bold yellow]" if element_hint else "[dim](Unlabeled)[/dim]"
    console.print(
        f"\n[bold cyan]🖱️ Computer Click:[/bold cyan] {label} | "
        f"Input: [dim]({x}, {y})[/dim] ➔ Pixel: [bold green]({target_px}, {target_py})[/bold green] on {w}x{h}"
    )

    # 1. Capture visual baseline if verification is active
    before_sample = screen_verifier.capture_screen_sample() if verify else None

    # 2. Execute Click
    if double_click:
        res = mouse_controller.double_click(x, y, button=button, element_hint=element_hint)
    elif button.lower() == "right":
        res = mouse_controller.right_click(x, y, element_hint=element_hint)
    else:
        res = mouse_controller.click(x, y, button=button, clicks=1, element_hint=element_hint)

    if res.get("status") != "success":
        return res

    # 3. Visual Verification Loop
    if verify and before_sample is not None:
        ver_info = screen_verifier.verify_action_effect(before_sample, settle_delay=0.35)
        res["verification"] = ver_info

    return res


def computer_type(
    text: str,
    x: Optional[float] = None,
    y: Optional[float] = None,
    element_hint: Optional[str] = None,
    press_enter: bool = False,
    clear_first: bool = False
) -> Dict[str, Any]:
    """
    Types text into an active input field. If coordinates (x, y) are provided,
    first clicks into that field to focus it before typing.
    """
    if x is not None and y is not None:
        click_res = computer_click(x, y, button="left", element_hint=element_hint or "input field", verify=False)
        if click_res.get("status") != "success":
            return click_res
        time.sleep(0.1)

    return keyboard_controller.type_text(
        text=text,
        press_enter=press_enter,
        clear_first=clear_first
    )


def computer_press_key(key_or_hotkey: str, count: int = 1) -> Dict[str, Any]:
    """
    Presses a single key or key combination (e.g. 'enter', 'esc', 'ctrl+c', 'win+r', 'alt+tab').
    """
    clean_k = key_or_hotkey.strip()
    console.print(f"\n[bold cyan]⌨️ Computer Key:[/bold cyan] [bold yellow]{clean_k}[/bold yellow] (count={count})")
    if "+" in clean_k or " " in clean_k:
        return keyboard_controller.press_hotkey(clean_k)
    else:
        return keyboard_controller.press_key(clean_k, count=count)


def computer_scroll(
    direction: str = "down",
    amount: int = 5,
    x: Optional[float] = None,
    y: Optional[float] = None
) -> Dict[str, Any]:
    """
    Scrolls the viewport up or down. If (x, y) are given, positions cursor over that region first.
    """
    console.print(f"\n[bold cyan]📜 Computer Scroll:[/bold cyan] {direction} by {amount} units")
    before_sample = screen_verifier.capture_screen_sample()
    res = mouse_controller.scroll(direction=direction, amount=amount, norm_x=x, norm_y=y)

    if res.get("status") == "success":
        ver_info = screen_verifier.verify_action_effect(before_sample, settle_delay=0.25)
        res["verification"] = ver_info

    return res


def computer_drag(
    from_x: float,
    from_y: float,
    to_x: float,
    to_y: float,
    button: str = "left"
) -> Dict[str, Any]:
    """
    Drags an item or window from (from_x, from_y) to (to_x, to_y) in normalized 0-1000 coordinates.
    """
    return mouse_controller.drag_to(
        from_norm_x=from_x,
        from_norm_y=from_y,
        to_norm_x=to_x,
        to_norm_y=to_y,
        button=button
    )


def computer_inspect_screen() -> Dict[str, Any]:
    """
    Returns the current screen resolution, cursor location, and active foreground window name.
    """
    info = CoordinateMapper.get_display_info()

    active_window = "Desktop"
    try:
        import win32gui
        hwnd = win32gui.GetForegroundWindow()
        active_window = win32gui.GetWindowText(hwnd) or "Desktop"
    except Exception:
        try:
            import pygetwindow as gw
            win = gw.getActiveWindow()
            if win:
                active_window = win.title
        except Exception:
            pass

    info["active_window"] = active_window
    return {"status": "success", "display": info}


def computer_reset_safety() -> Dict[str, Any]:
    """
    Clears action history and resets safety stop flag.
    """
    safety_guard.reset_emergency_stop()
    safety_guard.clear_history()
    return {"status": "success", "message": "Computer use safety guard reset."}


# Tool Registry Map for Live Mode
COMPUTER_ACTIONS = {
    "computer_click": computer_click,
    "computer_type": computer_type,
    "computer_press_key": computer_press_key,
    "computer_scroll": computer_scroll,
    "computer_drag": computer_drag,
    "computer_inspect_screen": computer_inspect_screen,
    "computer_reset_safety": computer_reset_safety,
}


def is_computer_use_tool(tool_name: str) -> bool:
    """Returns True if tool_name belongs to the Live Computer Use system."""
    return tool_name in COMPUTER_ACTIONS


def execute_computer_action(action_name: str, **kwargs) -> Dict[str, Any]:
    """Executes a computer use action by name with passed arguments."""
    handler = COMPUTER_ACTIONS.get(action_name)
    if not handler:
        return {"status": "error", "message": f"Unknown computer use action: '{action_name}'"}

    try:
        return handler(**kwargs)
    except Exception as e:
        return {"status": "error", "message": f"Execution error in {action_name}: {str(e)}"}
