"""
=============================================================================
F.R.I.D.A.Y 2.0 // DESKTOP SHORTCUT & ICON SYNC UTILITY
=============================================================================
Converts assets/logo.png -> assets/logo.ico and creates/updates Desktop shortcut
with custom logo icon and shell cache invalidation.
=============================================================================
"""

import os
import sys
import ctypes

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
LOGO_PNG = os.path.join(ASSETS_DIR, "logo.png")
LOGO_ICO = os.path.join(ASSETS_DIR, "logo.ico")
VBS_LAUNCHER = os.path.join(PROJECT_DIR, "run_friday_silent.vbs")


def ensure_ico():
    """Generates multi-resolution .ico from logo.png if missing or outdated."""
    if not os.path.exists(LOGO_PNG):
        print(f"[!] Warning: {LOGO_PNG} not found.")
        return False

    try:
        from PIL import Image
        img = Image.open(LOGO_PNG)
        # Multi-resolution icon for crisp rendering in all Windows view modes
        sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        img.save(LOGO_ICO, format="ICO", sizes=sizes)
        print(f"[OK] Generated Windows icon: {LOGO_ICO}")
        return True
    except Exception as e:
        print(f"[!] Error creating ICO: {e}")
        return False


def get_desktop_paths():
    """Finds all active Desktop paths (including OneDrive Desktop)."""
    desktops = set()

    # Special folder via Win32 Shell API
    try:
        import win32com.client
        ws = win32com.client.Dispatch("WScript.Shell")
        d = ws.SpecialFolders("Desktop")
        if os.path.exists(d):
            desktops.add(d)
    except Exception:
        pass

    user_profile = os.environ.get("USERPROFILE", "")
    if user_profile:
        std_desktop = os.path.join(user_profile, "Desktop")
        if os.path.exists(std_desktop):
            desktops.add(std_desktop)

    onedrive = os.environ.get("ONEDRIVE", "")
    if onedrive:
        od_desktop = os.path.join(onedrive, "Desktop")
        if os.path.exists(od_desktop):
            desktops.add(od_desktop)

    return list(desktops)


def update_desktop_shortcuts():
    """Creates or updates F.R.I.D.A.Y.lnk on desktop with the custom logo icon."""
    ensure_ico()
    desktops = get_desktop_paths()
    if not desktops:
        print("[!] No desktop folders found.")
        return

    try:
        import win32com.client
        ws = win32com.client.Dispatch("WScript.Shell")

        for d in desktops:
            lnk_path = os.path.join(d, "F.R.I.D.A.Y.lnk")
            shortcut = ws.CreateShortcut(lnk_path)
            shortcut.TargetPath = VBS_LAUNCHER
            shortcut.WorkingDirectory = PROJECT_DIR
            shortcut.Description = "F.R.I.D.A.Y 2.0 AI Super-Agent"
            if os.path.exists(LOGO_ICO):
                shortcut.IconLocation = f"{LOGO_ICO},0"
            shortcut.Save()
            print(f"[OK] Desktop Shortcut configured with custom logo: {lnk_path}")

        # Tell Windows Explorer to refresh icon cache immediately
        # SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_IDLIST = 0x0000
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        print("[OK] Windows Shell icon cache refreshed.")
    except Exception as e:
        print(f"[!] Failed to configure shortcut: {e}")


if __name__ == "__main__":
    update_desktop_shortcuts()
