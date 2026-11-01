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
import os
from typing import Dict, Any, Optional
from rich.console import Console

from Live.computer_use.coordinate_mapper import CoordinateMapper
from Live.computer_use.safety_guard import safety_guard
from Live.computer_use.mouse_controller import mouse_controller
from Live.computer_use.keyboard_controller import keyboard_controller
from Live.computer_use.screen_verifier import screen_verifier

console = Console()
DEBUG_LOG_FILE = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~")), "Friday", "live_computer_use.log")


def _log_to_file(entry: str):
    try:
        os.makedirs(os.path.dirname(DEBUG_LOG_FILE), exist_ok=True)
        with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {entry}\n")
    except Exception:
        pass


def _safe_log(msg: str):
    """Safely logs styled text across Windows cmd / charmap encoding environments."""
    try:
        console.print(msg)
    except Exception:
        try:
            # Fallback to plain stripped representation
            clean = msg.encode("ascii", "replace").decode("ascii")
            print(clean)
        except Exception:
            pass


def computer_click(
    visual_anchor: Optional[str] = None,
    element_hint: Optional[str] = None,
    x: float = 500,
    y: float = 500,
    button: str = "left",
    double_click: bool = False,
    verify: bool = True
) -> Dict[str, Any]:
    """
    Clicks on the desktop at normalized coordinates (0-1000) with closed-loop visual verification.
    visual_anchor forces the model to visually describe surrounding landmarks before estimating (x, y).
    """
    w, h = CoordinateMapper.get_screen_dimensions()
    target_px, target_py = CoordinateMapper.resolve_target_pixel(x, y, element_hint=element_hint)

    # Real-time console diagnostics so user and developer see exactly where Friday aims
    label = f"[bold yellow]'{element_hint or visual_anchor}'[/bold yellow]" if (element_hint or visual_anchor) else "[dim](Unlabeled)[/dim]"
    _safe_log(
        f"\n[bold cyan]🖱️ Computer Click:[/bold cyan] {label} | "
        f"Target: [dim]({x}, {y})[/dim] ➔ Pixel: [bold green]({target_px}, {target_py})[/bold green] on {w}x{h}"
        + (f" | Anchor: [dim]{visual_anchor}[/dim]" if visual_anchor else "")
    )
    _log_to_file(
        f"CLICK: target=({x}, {y}) -> pixel=({target_px}, {target_py}) on {w}x{h} | "
        f"hint='{element_hint}', anchor='{visual_anchor}', button={button}"
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

    _log_to_file(f"CLICK RESULT: status={res.get('status')}, action={res.get('action')}, res={res}")

    if res.get("status") not in ["success", "dispatched"]:
        return res

    # 3. Visual Verification Loop
    if verify and before_sample is not None:
        ver_info = screen_verifier.verify_action_effect(before_sample, settle_delay=0.35)
        res["verification"] = ver_info

    # Mark as 'dispatched' rather than absolute 'success' so model doesn't falsely assume target UI goal succeeded
    res["status"] = "dispatched"
    res["current_cursor"] = CoordinateMapper.get_current_cursor_info()
    res["live_vision_instruction"] = (
        f"Physical click dispatched at pixel ({target_px}, {target_py}) [norm: x={x}, y={y}]. "
        "Observe the next incoming live screen frame (with visible mouse cursor) to verify if the intended button/window opened. "
        "If the cursor landed slightly off, call 'computer_align_mouse(dx=..., dy=..., click_after=True)' to nudge it onto the button."
    )

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
        click_res = computer_click(x=x, y=y, button="left", element_hint=element_hint or "input field", verify=False)
        if click_res.get("status") not in ["success", "dispatched"]:
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
    _safe_log(f"\n[bold cyan]⌨️ Computer Key:[/bold cyan] [bold yellow]{clean_k}[/bold yellow] (count={count})")
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
    _safe_log(f"\n[bold cyan]📜 Computer Scroll:[/bold cyan] {direction} by {amount} units")
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


def computer_restore_mouse() -> Dict[str, Any]:
    """
    Restores the mouse cursor back to its previous original position before the last Friday action.
    Use this when a click missed, landed in the wrong place, or when Sir says you clicked wrong.
    """
    _safe_log("\n[bold cyan]↩️ Computer Restore Mouse:[/bold cyan] Reverting cursor to original position...")
    return mouse_controller.restore_cursor()


def computer_align_mouse(
    dx: float = 0,
    dy: float = 0,
    click_after: bool = True,
    button: str = "left",
    double_click: bool = False,
    element_hint: Optional[str] = None,
    reason: Optional[str] = None,
    verify: bool = True
) -> Dict[str, Any]:
    """
    Micro-adjusts the mouse cursor by (dx, dy) pixels relative to current position.
    When click_after=True, automatically clicks once aligned onto the target element.
    Provides visual feedback so Friday can verify the action from the live stream.
    """
    label = f"[bold yellow]'{element_hint}'[/bold yellow]" if element_hint else ""
    _safe_log(
        f"\n[bold cyan]🎯 Computer Align Mouse:[/bold cyan] {label} | "
        f"Nudge: [bold green]dx={dx}, dy={dy}[/bold green] | "
        f"Click After: [bold yellow]{click_after}[/bold yellow] | "
        f"Reason: [dim]{reason or 're-align onto target'}[/dim]"
    )

    before_sample = screen_verifier.capture_screen_sample() if (verify and click_after) else None

    res = mouse_controller.align_cursor(
        dx=dx,
        dy=dy,
        click_after=click_after,
        button=button,
        double_click=double_click,
        element_hint=element_hint
    )

    if res.get("status") not in ["success", "dispatched"]:
        return res

    if verify and before_sample is not None:
        ver_info = screen_verifier.verify_action_effect(before_sample, settle_delay=0.35)
        res["verification"] = ver_info

    if click_after:
        res["status"] = "dispatched"
        res["live_vision_instruction"] = (
            f"Cursor aligned by ({dx}, {dy}) to {res.get('new_pixel')} and clicked. "
            "Now observe the subsequent live screen video frame to visually verify if the intended button/window opened. "
            "Do NOT assume success blindly."
        )

    return res


# Tool Registry Map for Live Mode
COMPUTER_ACTIONS = {
    "computer_click": computer_click,
    "computer_type": computer_type,
    "computer_press_key": computer_press_key,
    "computer_scroll": computer_scroll,
    "computer_drag": computer_drag,
    "computer_inspect_screen": computer_inspect_screen,
    "computer_reset_safety": computer_reset_safety,
    "computer_restore_mouse": computer_restore_mouse,
    "computer_align_mouse": computer_align_mouse,
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
