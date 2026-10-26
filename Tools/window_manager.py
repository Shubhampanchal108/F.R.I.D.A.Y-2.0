"""
F.R.I.D.A.Y // Window Manager & Application Task Switcher
Switches focus between open application windows and lists user-facing running applications.
"""

import os
import re
import psutil
import ctypes
from ctypes import wintypes
import time

# Ignored system / driver / host processes to keep application list human-readable
SYSTEM_IGNORE = {
    "svchost", "conhost", "dllhost", "runtimebroker", "services", "system",
    "smss", "csrss", "wininit", "winlogon", "lsass", "fontdrvhost", "sihost",
    "taskhostw", "explorer", "searchhost", "startmenuexperiencehost", "shellexperiencehost",
    "ctfmon", "dwm", "spoolsv", "securityhealthservice", "audiodg", "wlanext",
    "aggregatorhost", "applicationframehost", "castsrv", "defendersessionhelper",
    "lsaiso", "mousoworker", "mpdefendercoreservice", "msmpeng", "nissrv", "trustedinstaller"
}

# Common application name aliases and synonym mappings
APP_ALIASES = {
    "vscode": ["code", "visual studio code", "antigravity", "antigravity ide"],
    "code": ["vscode", "visual studio code", "antigravity", "antigravity ide"],
    "vs code": ["vscode", "code", "visual studio code"],
    "visual studio code": ["code", "vscode"],
    "antigravity": ["code", "antigravity ide", "vscode"],
    "antigravity ide": ["code", "antigravity", "vscode"],
    "terminal": ["windowsterminal", "powershell", "cmd", "wt", "command prompt"],
    "cmd": ["cmd", "command prompt", "terminal"],
    "powershell": ["powershell", "pwsh", "terminal"],
    "browser": ["chrome", "msedge", "firefox", "brave", "opera"],
    "chrome": ["google chrome", "chrome"],
    "google chrome": ["chrome"],
    "edge": ["msedge", "microsoft edge"],
    "msedge": ["edge", "microsoft edge"],
    "microsoft edge": ["msedge", "edge"],
    "explorer": ["explorer", "file explorer"],
    "files": ["explorer", "file explorer"],
    "file explorer": ["explorer"],
    "word": ["winword", "microsoft word"],
    "excel": ["excel", "microsoft excel"],
    "spotify": ["spotify"],
    "notepad": ["notepad"],
    "settings": ["systemsettings", "applicationframehost"],
    "calculator": ["calculator", "calc", "calculatorapp"],
}

# Win32 Constants
SW_RESTORE = 9
SW_SHOW = 5
DWMWA_CLOAKED = 14
VK_MENU = 0x12
KEYEVENTF_KEYUP = 0x0002


def _clean_str(s: str) -> str:
    """Removes all non-alphanumeric characters for fuzzy punctuation-agnostic comparison."""
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def _get_visible_windows() -> list:
    """
    Discovers all visible, user-facing top-level desktop windows.
    Properly attaches to the interactive 'Default' desktop to work from any thread context.
    """
    user32 = ctypes.windll.user32
    dwmapi = ctypes.windll.dwmapi

    # Ensure the current thread is attached to the interactive user desktop
    hdesk = None
    try:
        hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass

    windows = []

    def enum_proc(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True

        # Filter out cloaked/suspended UWP background windows (Windows 10/11)
        cloaked = wintypes.DWORD()
        if dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked)) == 0:
            if cloaked.value != 0:
                return True

        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True

        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value.strip()

        # Ignore system desktop / helper backgrounds
        if not title or title in {"Program Manager", "Microsoft Text Input Application", "Default IME", "MSCTFIME UI"}:
            return True

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        pname = ""
        try:
            pname = psutil.Process(pid.value).name()
        except Exception:
            pass

        base_pname = pname[:-4].lower() if pname.lower().endswith(".exe") else pname.lower()

        windows.append({
            "hwnd": hwnd,
            "title": title,
            "process_name": pname,
            "process_base": base_pname,
            "pid": pid.value
        })
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    cb = WNDENUMPROC(enum_proc)

    if hdesk:
        user32.EnumDesktopWindows(hdesk, cb, 0)
    else:
        user32.EnumWindows(cb, 0)

    return windows


def _score_window(query: str, window: dict) -> int:
    """
    Scores how closely a window matches the user's requested application name.
    """
    q_raw = str(query).lower().strip()
    if q_raw.endswith(".exe"):
        q_raw = q_raw[:-4]

    q_clean = _clean_str(q_raw)
    p_base = window["process_base"]
    p_clean = _clean_str(p_base)
    title_lower = window["title"].lower()
    title_clean = _clean_str(title_lower)

    # Gather search terms including configured aliases
    search_terms = {q_raw}
    if q_raw in APP_ALIASES:
        search_terms.update(APP_ALIASES[q_raw])
    for alias, targets in APP_ALIASES.items():
        if q_raw in targets or any(q_raw in t for t in targets):
            search_terms.add(alias)
            search_terms.update(targets)

    score = 0

    # 1. Process name matches (highest weight)
    if p_base == q_raw or p_clean == q_clean:
        score += 150
    elif any(p_base == term for term in search_terms):
        score += 130
    elif q_clean and q_clean in p_clean:
        score += 100
    elif any(_clean_str(term) in p_clean for term in search_terms if _clean_str(term)):
        score += 85

    # 2. Window title matches
    if title_lower == q_raw or title_clean == q_clean:
        score += 140
    elif q_clean and q_clean in title_clean:
        score += 90
    elif any(_clean_str(term) in title_clean for term in search_terms if _clean_str(term)):
        score += 75

    # 3. Individual token matches
    tokens = [t for t in re.split(r"[\s\-_.]+", q_raw) if len(t) > 2]
    for t in tokens:
        t_clean = _clean_str(t)
        if t_clean in p_clean:
            score += 40
        if t_clean in title_clean:
            score += 35

    return score


def _bring_to_foreground(hwnd: int) -> bool:
    """
    Reliably brings an HWND to the foreground by restoring minimized state
    and bypassing the Windows foreground lock using AttachThreadInput and simulated ALT key.
    """
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Restore desktop context
    try:
        hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass

    # 1. Restore window if minimized
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    else:
        user32.ShowWindow(hwnd, SW_SHOW)

    # 2. Bypass Windows SetForegroundWindow lock
    fg_hwnd = user32.GetForegroundWindow()
    fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
    cur_thread = kernel32.GetCurrentThreadId()

    attached = False
    if fg_thread and fg_thread != cur_thread:
        attached = bool(user32.AttachThreadInput(cur_thread, fg_thread, True))

    try:
        # Simulate ALT key tap to grant foreground activation privilege
        user32.keybd_event(VK_MENU, 0, 0, 0)
        user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)

        user32.AllowSetForegroundWindow(-1)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
    except Exception:
        pass
    finally:
        if attached:
            try:
                user32.AttachThreadInput(cur_thread, fg_thread, False)
            except Exception:
                pass

    # 3. SwitchToThisWindow provides an extra guarantee
    try:
        user32.SwitchToThisWindow(hwnd, True)
    except Exception:
        pass

    return True


def list_running_apps(limit: int = 25) -> dict:
    """
    Returns a clean, sorted list of user-facing running desktop applications and visible windows.
    Filters out background Windows operating system processes.
    """
    try:
        # Get visible window titles first
        visible_windows = _get_visible_windows()
        window_titles = [w["title"] for w in visible_windows]

        active_apps = set()
        for proc in psutil.process_iter(['name', 'cpu_percent']):
            try:
                name = proc.info.get('name')
                if not name:
                    continue
                clean = name.lower()
                if clean.endswith(".exe"):
                    clean = clean[:-4]
                if clean not in SYSTEM_IGNORE:
                    clean_display = name[:-4] if name.lower().endswith(".exe") else name
                    active_apps.add(clean_display)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        sorted_apps = sorted(list(active_apps), key=lambda x: x.lower())
        return {
            "status": "success",
            "total_user_apps": len(sorted_apps),
            "open_windows": window_titles,
            "running_apps": sorted_apps[:limit]
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to list running apps: {str(e)}"}


def focus_window(app_name: str) -> dict:
    """
    Brings an existing application window to the foreground on Shubham sir's screen.
    app_name: Name of the application or title (e.g., 'chrome', 'code', 'vscode', 'notepad', 'spotify', 'telegram').
    """
    if not app_name or not str(app_name).strip():
        return {"status": "error", "message": "Application name is required."}

    target = str(app_name).strip()

    try:
        windows = _get_visible_windows()
        if not windows:
            return {
                "status": "error",
                "action": "focus_window",
                "message": f"No open desktop windows found to focus '{target}'."
            }

        # Score all windows against the requested app_name
        scored = []
        for w in windows:
            score = _score_window(target, w)
            if score > 0:
                scored.append((score, w))

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            best_match = scored[0][1]

            _bring_to_foreground(best_match["hwnd"])

            return {
                "status": "success",
                "action": "focus_window",
                "app_name": app_name,
                "window_title": best_match["title"],
                "process_name": best_match["process_name"],
                "pid": best_match["pid"],
                "message": f"Brought '{best_match['title']}' to the foreground, Sir."
            }

        # If no direct match in top-level visible windows, provide open windows list
        open_list = [w["title"] for w in windows]
        return {
            "status": "error",
            "action": "focus_window",
            "message": f"Could not find an open window matching '{app_name}'. The application may not be running or is minimized to system tray.",
            "open_windows": open_list
        }

    except Exception as e:
        return {"status": "error", "message": f"Window focus error: {str(e)}"}
