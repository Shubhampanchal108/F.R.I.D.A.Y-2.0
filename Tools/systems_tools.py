import psutil
import ctypes
from datetime import datetime
import requests
import time
import pyautogui
from AppOpener import open as appopen
import pyautogui


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
    cpu_usage = psutil.cpu_percent(interval=1)

    physical_cpus = psutil.cpu_count(logical=False)
    logical_cpus = psutil.cpu_count(logical=True)

    cpu_freq = psutil.cpu_freq()

    return {
        "cpu_usage_percent": cpu_usage,
        "physical_cores": physical_cpus,
        "logical_cores": logical_cpus,
        "frequency_mhz": cpu_freq.current if cpu_freq else None
    }



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

        appopen(
            app,
            match_closest=False,
            output=True,
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
    
def close_app(app):
    try :
        pyautogui.hotkey('alt', 'f4')
        return {
            "success": True,
            "message": "closed successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "message": e
        }
