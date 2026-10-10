"""
=============================================================================
F.R.I.D.A.Y 2.0 // AUTO-START INTERNET SENTINEL & SYSTEM BOOTSTRAPPER
=============================================================================
Monitors for active internet connectivity upon Windows startup, announces
system status with Jarvis-class neural voice, and launches Friday seamlessly.
=============================================================================
"""

import os
import sys
import time
import socket
import subprocess
import argparse

# Ensure current directory is the project directory
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)

# Path to pythonw and target scripts
PYTHONW_EXE = os.path.join(PROJECT_DIR, ".venv", "Scripts", "pythonw.exe")
PYTHON_EXE = os.path.join(PROJECT_DIR, ".venv", "Scripts", "python.exe")
WIDGET_SCRIPT = os.path.join(PROJECT_DIR, "friday_widget.py")

# Fallback to system python if venv pythonw not found
if not os.path.exists(PYTHONW_EXE):
    PYTHONW_EXE = sys.executable


def is_friday_widget_running():
    """Checks if friday_widget.py is already active to prevent duplicate instances."""
    try:
        import psutil
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] == current_pid:
                    continue
                cmdline = proc.info.get('cmdline') or []
                cmd_str = " ".join(cmdline).lower()
                if "friday_widget.py" in cmd_str:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass
    return False


def is_internet_available(timeout=2.0):
    """Fast, low-latency socket ping to reliable DNS hosts."""
    test_hosts = [
        ("8.8.8.8", 53),        # Google DNS
        ("1.1.1.1", 53),        # Cloudflare DNS
        ("208.67.222.222", 53)  # OpenDNS
    ]
    for host, port in test_hosts:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((host, port))
            s.close()
            return True
        except Exception:
            continue
    return False


def play_startup_announcement():
    """Speaks the JARVIS online confirmation."""
    try:
        from speak import speak
        greeting = "Internet access detected. All systems online, Boss."
        # Spoken audio with high priority, blocking until audio finishes
        speak(greeting, allow_interrupt=False, priority=1, block=True)
    except Exception as e:
        # Fallback to Windows native sound / speech if speak module fails
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak("Internet connected. Systems online, Boss.")
        except Exception:
            pass


def launch_friday_widget():
    """Launches the Friday Floating Corner Widget in the background."""
    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS

    subprocess.Popen(
        [PYTHONW_EXE, WIDGET_SCRIPT],
        cwd=PROJECT_DIR,
        creationflags=creation_flags,
        close_fds=True
    )


def main():
    parser = argparse.ArgumentParser(description="Friday Auto-Start Sentinel")
    parser.add_argument("--now", action="store_true", help="Launch immediately without waiting for internet")
    parser.add_argument("--silent", action="store_true", help="Launch without voice announcement")
    args = parser.parse_args()

    # If Friday is already running, exit cleanly
    if is_friday_widget_running():
        return

    # If --now is specified, start immediately
    if not args.now:
        # Poll until internet connection is active
        while not is_internet_available():
            time.sleep(3.0)

    # Re-check in case another instance started while waiting for internet
    if is_friday_widget_running():
        return

    # 1. Announce system readiness via voice
    if not args.silent:
        play_startup_announcement()

    # 2. Launch the Friday Corner HUD Widget
    launch_friday_widget()


if __name__ == "__main__":
    main()
