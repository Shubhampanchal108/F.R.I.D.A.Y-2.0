"""
F.R.I.D.A.Y // Window Manager & Application Task Switcher
Switches focus between open application windows and lists user-facing running applications.
"""

import os
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


def list_running_apps(limit: int = 25) -> dict:
    """
    Returns a clean, sorted list of user-facing running desktop applications.
    Filters out background Windows operating system processes.
    """
    try:
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
                    # Keep original casing if readable
                    clean_display = name[:-4] if name.lower().endswith(".exe") else name
                    active_apps.add(clean_display)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        sorted_apps = sorted(list(active_apps), key=lambda x: x.lower())
        return {
            "status": "success",
            "total_user_apps": len(sorted_apps),
            "running_apps": sorted_apps[:limit]
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to list running apps: {str(e)}"}


def focus_window(app_name: str) -> dict:
    """
    Brings an existing application window to the foreground on Shubham sir's screen.
    app_name: Name of the application (e.g., 'chrome', 'code', 'notepad', 'spotify', 'telegram').
    """
    if not app_name or not str(app_name).strip():
        return {"status": "error", "message": "Application name is required."}

    target = str(app_name).lower().strip()

    # 1. Try AppOpener first (handles window restore and focus automatically)
    try:
        from AppOpener import open as appopen
        appopen(target, match_closest=True, output=False, throw_error=True)
        return {
            "status": "success",
            "action": "focus_window",
            "message": f"Brought '{app_name}' to the foreground, Sir."
        }
    except Exception:
        pass

    # 2. Try native Windows EnumWindows & SetForegroundWindow
    try:
        user32 = ctypes.windll.user32
        SW_RESTORE = 9

        found_hwnd = None

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        def enum_cb(hwnd, lparam):
            nonlocal found_hwnd
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.lower()
                    if target in title:
                        found_hwnd = hwnd
                        return False  # stop enumeration
            return True

        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

        if found_hwnd:
            user32.ShowWindow(found_hwnd, SW_RESTORE)
            user32.SetForegroundWindow(found_hwnd)
            return {
                "status": "success",
                "action": "focus_window",
                "message": f"Focused application '{app_name}' successfully."
            }
    except Exception as e:
        return {"status": "error", "message": f"Window focus error: {str(e)}"}

    return {
        "status": "error",
        "message": f"Could not find an open window matching '{app_name}'."
    }
