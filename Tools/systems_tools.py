import psutil
import ctypes
import subprocess
from datetime import datetime
import requests
import time
import pyautogui
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc
import threading



def greet():
    current_hour = datetime.now().hour

    if 5 <= current_hour < 12:
        return "Good Morning Sir!"
    elif 12 <= current_hour < 17:
        return "Good Afternoon Sir!"
    elif 17 <= current_hour < 21:
        return "Good Evening sir!"
    else:
        return "Hello sir!, Sir I think it's late night and you should sleep now."


def find_my_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=10)
        data = response.json()

        return {
            "ip": data["ip"]
        }

    except Exception as e:
        return {
            "error": str(e)
        }


def get_battery_status():
    battery = psutil.sensors_battery()

    if battery is None:
        return {
            "error": "Battery information not available"
        }

    percent = battery.percent
    plugged = battery.power_plugged

    return {
        "battery_percentage": percent,
        "charging": plugged,
        "status": "Charging" if plugged else "Not Charging",
        "low_battery_warning": percent <= 30 and not plugged
    }


def get_cpu_status():
    cpu_usage = psutil.cpu_percent(interval=0.5)

    physical_cpus = psutil.cpu_count(logical=False)
    logical_cpus = psutil.cpu_count(logical=True)

    cpu_freq = psutil.cpu_freq()
    ram = psutil.virtual_memory()

    return {
        "cpu_usage_percent": cpu_usage,
        "physical_cores": physical_cpus,
        "logical_cores": logical_cpus,
        "frequency_mhz": cpu_freq.current if cpu_freq else None,
        "ram_usage_percent": ram.percent,
        "ram_used_gb": round(ram.used / (1024**3), 1),
        "ram_total_gb": round(ram.total / (1024**3), 1)
    }


def get_top_resource_consumers(n=2):
    """Identify top processes consuming CPU for proactive system monitoring."""
    try:
        # Prime psutil counters
        for p in psutil.process_iter(['name']):
            try:
                p.cpu_percent(None)
            except Exception:
                pass
        time.sleep(0.15)

        proc_list = []
        for p in psutil.process_iter(['name']):
            try:
                name = p.info.get('name')
                if not name or "idle" in name.lower() or "system idle" in name.lower():
                    continue
                cpu = p.cpu_percent(None)
                if cpu and cpu > 1.0:
                    proc_list.append((name, round(cpu, 1)))
            except Exception:
                pass
        proc_list.sort(key=lambda x: x[1], reverse=True)
        return proc_list[:n]
    except Exception:
        return []




def empty_recycle_bin():
    try:
        SHERB_NOCONFIRMATION = 0x00000001
        SHERB_NOPROGRESSUI = 0x00000002
        SHERB_NOSOUND = 0x00000004

        ctypes.windll.shell32.SHEmptyRecycleBinW(
            None,
            None,
            SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
        )

        return {
            "success": True,
            "message": "Recycle bin emptied successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def open_application(app: str):
    try:
        from AppOpener import open as appopen
        appopen(
            app,
            match_closest=False,
            output=False,
            throw_error=True
        )

        return {
            "status": "success",
            "app": app,
            "method": "appopener"
        }

    except Exception:
        try:
            pyautogui.press('win')
            time.sleep(1)

            clean_app = app.replace(".", "").lower().strip()
            pyautogui.typewrite(clean_app)
            time.sleep(1)

            pyautogui.press('enter')

            return {
                "status": "success",
                "app": app,
                "method": "windows_search"
            }

        except Exception as e:
            return {"error": str(e)}
    
def close_app(app: str = None):
    try:
        # If no specific app is named, or user asks to close current/active window
        if not app or str(app).lower().strip() in ["current", "active", "this", "window", "active_window"]:
            pyautogui.hotkey('alt', 'f4')
            return {
                "status": "success",
                "action": "close_app",
                "message": "Active window closed successfully."
            }

        target = str(app).lower().strip().replace(".exe", "")

        # 1. Try process matching and termination via psutil
        closed_any = False
        for p in psutil.process_iter(['name', 'pid']):
            try:
                p_name = (p.info.get('name') or "").lower()
                if target in p_name:
                    p.terminate()
                    closed_any = True
            except Exception:
                pass

        if closed_any:
            return {
                "status": "success",
                "app": app,
                "action": "close_app",
                "message": f"Closed '{app}' successfully."
            }

        # 2. Try taskkill command
        res = subprocess.run(["taskkill", "/f", "/im", f"{target}.exe"], capture_output=True, text=True)
        if res.returncode == 0:
            return {
                "status": "success",
                "app": app,
                "action": "close_app",
                "message": f"Closed '{app}' successfully."
            }

        # 3. Try AppOpener.close with exact name match
        try:
            from AppOpener import close as appclose
            status = appclose(target, match_closest=False, output=False, throw_error=True)
            if status:
                return {
                    "status": "success",
                    "app": app,
                    "action": "close_app",
                    "message": f"Closed '{app}' successfully."
                }
        except Exception:
            pass

        return {
            "status": "error",
            "action": "close_app",
            "message": f"Could not find running application matching '{app}'."
        }

    except Exception as e:
        return {
            "status": "error",
            "action": "close_app",
            "message": f"Error closing application: {str(e)}"
        }

def volume_up(step=10):
    try:
        step = int(step)
        if step <= 0:
            raise ValueError("Step must be positive")

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        current = volume.GetMasterVolumeLevelScalar()
        new_volume = min(1.0, current + step / 100)

        volume.SetMasterVolumeLevelScalar(new_volume, None)

        return {
            "status": "success",
            "action": "volume_up",
            "message": "Volume increased",
            "previous": round(current * 100, 1),
            "current": round(new_volume * 100, 1)
        }

    except ValueError as e:
        return {
            "status": "error",
            "code": "INVALID_STEP",
            "message": str(e)
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "VOLUME_CONTROL_FAILED",
            "message": str(e)
        }

def volume_down(step=10):
    try:
        step = int(step)
        if step <= 0:
            raise ValueError("Step must be positive")

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        current = volume.GetMasterVolumeLevelScalar()
        new_volume = max(0.0, current - step / 100)

        volume.SetMasterVolumeLevelScalar(new_volume, None)

        return {
            "status": "success",
            "action": "volume_down",
            "message": "Volume decreased",
            "previous": round(current * 100, 1),
            "current": round(new_volume * 100, 1)
        }

    except ValueError as e:
        return {
            "status": "error",
            "code": "INVALID_STEP",
            "message": str(e)
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "VOLUME_CONTROL_FAILED",
            "message": str(e)
        }

def brightness_up(step=10):
    try:
        step = int(step)
        if step <= 0:
            raise ValueError("Step must be positive")

        current = sbc.get_brightness(display=0)[0]
        new_brightness = min(100, current + step)

        sbc.set_brightness(new_brightness)

        return {
            "status": "success",
            "action": "brightness_up",
            "message": "Brightness increased",
            "previous": current,
            "current": new_brightness
        }

    except ValueError as e:
        return {
            "status": "error",
            "code": "INVALID_STEP",
            "message": str(e)
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "BRIGHTNESS_CONTROL_FAILED",
            "message": str(e)
        }

def brightness_down(step=10):
    try:
        step = int(step)
        if step <= 0:
            raise ValueError("Step must be positive")

        current = sbc.get_brightness(display=0)[0]
        new_brightness = max(0, current - step)

        sbc.set_brightness(new_brightness)

        return {
            "status": "success",
            "action": "brightness_down",
            "message": "Brightness decreased",
            "previous": current,
            "current": new_brightness
        }

    except ValueError as e:
        return {
            "status": "error",
            "code": "INVALID_STEP",
            "message": str(e)
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "BRIGHTNESS_CONTROL_FAILED",
            "message": str(e)
        }

def mute_volume():
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        # Mute the volume
        volume.SetMute(1, None)  # 1 = mute

        current_level = volume.GetMasterVolumeLevelScalar()  # still returns volume level

        return {
            "status": "success",
            "action": "mute_volume",
            "message": "Volume muted",
            "current_level": round(current_level * 100, 1),
            "muted": True
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "VOLUME_MUTE_FAILED",
            "message": str(e),
            "muted": False
        }

def unmute_volume():
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        # Unmute the volume
        volume.SetMute(0, None)  # 0 = unmute
        current_level = volume.GetMasterVolumeLevelScalar()

        return {
            "status": "success",
            "action": "unmute_volume",
            "message": "Volume unmuted",
            "current_level": round(current_level * 100, 1),
            "muted": False
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "VOLUME_UNMUTE_FAILED",
            "message": str(e),
            "muted": None
        }

def minimize_active_window():
    try:
        pyautogui.hotkey('alt', 'space')
        time.sleep(0.2)
        pyautogui.press('n')

        return {
            "status": "success",
            "action": "minimize_active_window",
            "message": "Active window minimized successfully"
        }

    except Exception as e:
        return {
            "status": "error",
            "action": "minimize_active_window",
            "error": str(e)
        }
    
def maximize_active_window():
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        SW_MAXIMIZE = 3
        if hwnd:
            user32.ShowWindow(hwnd, SW_MAXIMIZE)
        prev_fs = pyautogui.FAILSAFE
        try:
            pyautogui.FAILSAFE = False
            pyautogui.hotkey('win', 'up')
        finally:
            pyautogui.FAILSAFE = prev_fs

        return {
            "status": "success",
            "action": "maximize_active_window",
            "message": "Active window maximized successfully."
        }
    except Exception:
        try:
            prev_fs = pyautogui.FAILSAFE
            try:
                pyautogui.FAILSAFE = False
                pyautogui.hotkey('win', 'up')
            finally:
                pyautogui.FAILSAFE = prev_fs
            return {
                "status": "success",
                "action": "maximize_active_window",
                "message": "Active window maximized successfully."
            }
        except Exception as e:
            return {
                "status": "error",
                "action": "maximize_active_window",
                "message": str(e)
            }


# =============================================================================
# SYSTEM POWER & WORKSTATION CONTROLS (LOCK, SLEEP, SHUTDOWN, RESTART)
# =============================================================================

def lock_pc():
    """Immediately locks the Windows workstation screen."""
    try:
        def _perform_lock():
            time.sleep(0.5)  # Brief pause to allow voice confirmation before locking
            ctypes.windll.user32.LockWorkStation()

        t = threading.Thread(target=_perform_lock, daemon=True)
        t.start()
        return {
            "status": "success",
            "action": "lock_pc",
            "message": "Workstation locked successfully."
        }
    except Exception as e:
        return {
            "status": "error",
            "action": "lock_pc",
            "message": str(e)
        }


def sleep_pc():
    """Puts the computer into sleep/suspend mode."""
    def _perform_sleep():
        time.sleep(1.5)  # Allow Friday to respond/speak before sleeping
        try:
            # Try via ctypes powrprof
            ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
        except Exception:
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState([System.Windows.Forms.PowerState]::Suspend, $false, $false)"],
                    shell=True
                )
            except Exception:
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], shell=True)

    try:
        t = threading.Thread(target=_perform_sleep, daemon=True)
        t.start()
        return {
            "status": "success",
            "action": "sleep_pc",
            "message": "Entering sleep mode."
        }
    except Exception as e:
        return {
            "status": "error",
            "action": "sleep_pc",
            "message": str(e)
        }


def shutdown_pc(delay: int = 5):
    """
    Shuts down the Windows computer after a specified delay in seconds.
    Default delay is 5 seconds to allow Friday to finish speaking.
    """
    try:
        try:
            delay = int(delay)
        except (ValueError, TypeError):
            delay = 5
        if delay < 0:
            delay = 0

        # /s = shutdown, /t = timer in seconds
        subprocess.run(["shutdown", "/s", "/t", str(delay)], check=True, shell=True)
        return {
            "status": "success",
            "action": "shutdown_pc",
            "delay": delay,
            "message": f"System will shut down in {delay} seconds."
        }
    except Exception as e:
        return {
            "status": "error",
            "action": "shutdown_pc",
            "message": str(e)
        }


def restart_pc(delay: int = 5):
    """
    Restarts the Windows computer after a specified delay in seconds.
    Default delay is 5 seconds to allow Friday to finish speaking.
    """
    try:
        try:
            delay = int(delay)
        except (ValueError, TypeError):
            delay = 5
        if delay < 0:
            delay = 0

        # /r = restart, /t = timer in seconds
        subprocess.run(["shutdown", "/r", "/t", str(delay)], check=True, shell=True)
        return {
            "status": "success",
            "action": "restart_pc",
            "delay": delay,
            "message": f"System will restart in {delay} seconds."
        }
    except Exception as e:
        return {
            "status": "error",
            "action": "restart_pc",
            "message": str(e)
        }


def cancel_shutdown():
    """Cancels a pending shutdown or restart if one is in progress."""
    try:
        res = subprocess.run(["shutdown", "/a"], capture_output=True, text=True, shell=True)
        if res.returncode == 0:
            return {
                "status": "success",
                "action": "cancel_shutdown",
                "message": "Scheduled shutdown or restart has been cancelled."
            }
        else:
            return {
                "status": "info",
                "action": "cancel_shutdown",
                "message": "No scheduled shutdown or restart was in progress."
            }
    except Exception as e:
        return {
            "status": "error",
            "action": "cancel_shutdown",
            "message": f"Unable to cancel shutdown: {str(e)}"
        }


def system_power_control(action: str, delay: int = 5):
    """
    Controls computer power states: lock screen, sleep, shutdown, restart, or cancel shutdown.

    Parameters:
        action (str): One of 'lock', 'sleep', 'shutdown', 'restart', 'cancel'.
        delay (int): Delay in seconds before shutdown or restart (default: 5).
    """
    if not action:
        return {
            "status": "error",
            "message": "Please specify a power action: 'lock', 'sleep', 'shutdown', 'restart', or 'cancel'."
        }

    act = str(action).lower().strip()
    if act in ["lock", "lock_screen", "lock_pc", "lock_workstation"]:
        return lock_pc()
    elif act in ["sleep", "suspend", "sleep_pc", "standby"]:
        return sleep_pc()
    elif act in ["shutdown", "poweroff", "power_off", "turn_off", "shutdown_pc"]:
        return shutdown_pc(delay=delay)
    elif act in ["restart", "reboot", "restart_pc"]:
        return restart_pc(delay=delay)
    elif act in ["cancel", "cancel_shutdown", "abort", "abort_shutdown"]:
        return cancel_shutdown()
    else:
        return {
            "status": "error",
            "message": f"Unknown power action '{action}'. Supported actions: 'lock', 'sleep', 'shutdown', 'restart', 'cancel'."
        }