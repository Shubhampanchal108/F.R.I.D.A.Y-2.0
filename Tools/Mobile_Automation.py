import os
import sys
import time
import subprocess
from urllib.parse import quote
import re

ADB_PATH = "adb" 
ADB_PORT = "5555"

# Tracks active device serial or IP:PORT
ACTIVE_DEVICE = None


# ---------------- Mobile Connection & Device Resolution ----------------
def is_mobile_connected():
    """Returns (True, [device_list]) if any device is connected and authorized."""
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            [ADB_PATH, "devices"],
            capture_output=True,
            text=True,
            creationflags=creation_flags
        )
        lines = result.stdout.strip().split("\n")
        devices = []
        for line in lines[1:]:
            parts = line.strip().split()
            # Only count devices with status "device" (exclude "offline", "unauthorized")
            if len(parts) >= 2 and parts[1] == "device" and not line.strip().startswith("*"):
                devices.append(parts[0])

        if len(devices) > 0:
            return True, devices
        else:
            return False, []
    except Exception:
        return False, []


def get_target_device():
    """
    Resolves the target ADB device serial or IP:PORT.
    Ensures that when multiple devices (e.g. USB + Wi-Fi) exist,
    ADB commands will not fail with 'more than one device/emulator'.
    """
    global ACTIVE_DEVICE
    connected, devices = is_mobile_connected()
    if not connected or not devices:
        ACTIVE_DEVICE = None
        return None

    # If previously set active device is still connected and online, use it
    if ACTIVE_DEVICE and ACTIVE_DEVICE in devices:
        return ACTIVE_DEVICE

    # Prioritize wireless/network device (contains ':')
    for d in devices:
        if ":" in d:
            ACTIVE_DEVICE = d
            return d

    # Otherwise use the first available online device (e.g. USB)
    ACTIVE_DEVICE = devices[0]
    return ACTIVE_DEVICE


def run_cmd(command):
    """
    Executes a shell command. Automatically injects -s <target_device>
    if calling ADB shell without -s when devices are connected.
    """
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    cmd_str = command.strip()

    # Automatically add -s <target> if calling adb shell without -s
    target = get_target_device()
    if target and "-s " not in cmd_str:
        if cmd_str.startswith(f"{ADB_PATH} shell"):
            cmd_str = cmd_str.replace(f"{ADB_PATH} shell", f'"{ADB_PATH}" -s {target} shell', 1)
        elif cmd_str.startswith("adb shell"):
            cmd_str = cmd_str.replace("adb shell", f'"{ADB_PATH}" -s {target} shell', 1)
        elif cmd_str.startswith(f"{ADB_PATH} tcpip"):
            cmd_str = cmd_str.replace(f"{ADB_PATH} tcpip", f'"{ADB_PATH}" -s {target} tcpip', 1)

    try:
        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=True,
            text=True,
            creationflags=creation_flags
        )
        if result.returncode != 0:
            err = (result.stderr or "").strip()
            if err:
                print(f"[ADB CMD ERROR] {cmd_str} -> {err}")
        return (result.stdout or "").strip()
    except Exception as e:
        print(f"[ADB CMD EXCEPTION] {cmd_str} -> {e}")
        return ""


def run_adb_shell(subcommand, device=None):
    """Executes an adb shell command on the target device using -s <device>."""
    target = device or get_target_device()
    if target:
        cmd = f'"{ADB_PATH}" -s {target} shell {subcommand}'
    else:
        cmd = f'"{ADB_PATH}" shell {subcommand}'
    return run_cmd(cmd)


def check_connection_json(**kwargs):
    connected, devices = is_mobile_connected()
    target = get_target_device()
    if connected:
        return {
            "status": "success",
            "message": f"Mobile connected ({target or ', '.join(devices)})",
            "devices": devices,
            "active_device": target
        }
    else:
        return {
            "status": "error",
            "code": "NO_DEVICE",
            "message": "No mobile device connected. Please connect phone via USB or Wireless ADB."
        }


# ---------------- Mobile Connect ----------------
def connect_mobile_with_bat(ip_address=None, device_ip=None, ip=None, **kwargs):
    global ACTIVE_DEVICE
    target_ip = ip_address or device_ip or ip or kwargs.get("ip_address") or kwargs.get("device_ip") or kwargs.get("ip")

    # If no IP provided, check if a device is connected via USB and query its Wi-Fi IP
    if not target_ip:
        try:
            connected, devices = is_mobile_connected()
            usb_devs = [d for d in devices if ":" not in d]
            usb_flag = f"-s {usb_devs[0]} " if usb_devs else ""
            route_out = run_cmd(f'"{ADB_PATH}" {usb_flag}shell ip route')
            match = re.search(r'src\s+(\d+\.\d+\.\d+\.\d+)', route_out)
            if match:
                target_ip = match.group(1)
        except Exception:
            pass

    if not target_ip:
        return {
            "status": "error",
            "code": "IP_REQUIRED",
            "message": "Mobile IP address required. Please specify your phone's Wi-Fi IP address (e.g., 192.168.1.3)."
        }

    target_ip = str(target_ip).strip()
    port = ADB_PORT
    if ":" in target_ip:
        parts = target_ip.split(":")
        target_ip = parts[0].strip()
        if len(parts) > 1 and parts[1].strip():
            port = parts[1].strip()

    target_endpoint = f"{target_ip}:{port}"
    print(f"📱 Target Device: {target_endpoint}")

    # 📡 Enable TCPIP Mode (target USB device if attached)
    print("📡 Switching to TCPIP mode...")
    connected, devices = is_mobile_connected()
    usb_devs = [d for d in devices if ":" not in d]
    usb_flag = f"-s {usb_devs[0]} " if usb_devs else ""
    run_cmd(f'"{ADB_PATH}" {usb_flag}tcpip {port}')
    time.sleep(1)

    # 🔌 Disconnect any stale session for this endpoint
    run_cmd(f'"{ADB_PATH}" disconnect {target_endpoint}')
    time.sleep(0.5)

    # 🚀 Connect device
    print(f"🚀 Connecting to {target_endpoint} ...")
    output = run_cmd(f'"{ADB_PATH}" connect {target_endpoint}')
    print(f"ADB output: {output}")

    # Check connection
    connected, devices = is_mobile_connected()
    is_success = (target_endpoint in devices) or (connected and any(target_ip in d for d in devices))

    if not is_success:
        print("🔄 Retrying connection with fresh ADB server...")
        run_cmd(f'"{ADB_PATH}" kill-server')
        time.sleep(1)
        run_cmd(f'"{ADB_PATH}" start-server')
        time.sleep(1)
        output = run_cmd(f'"{ADB_PATH}" connect {target_endpoint}')
        connected, devices = is_mobile_connected()
        is_success = (target_endpoint in devices) or (connected and any(target_ip in d for d in devices))

    if is_success:
        ACTIVE_DEVICE = target_endpoint if target_endpoint in devices else devices[0]
        return {
            "status": "success",
            "action": "connect_mobile",
            "device_ip": target_ip,
            "port": port,
            "active_device": ACTIVE_DEVICE,
            "message": f"Successfully connected to mobile device at {target_endpoint}."
        }
    else:
        return {
            "status": "error",
            "code": "CONNECTION_FAILED",
            "message": f"Could not connect to {target_endpoint}. Output: {output}. Please ensure Wireless Debugging is ON in Android Developer Options and on the same Wi-Fi."
        }


# ---------------- Mobile Controls ----------------
def unlock_device(pin_code=None, pin=None, **kwargs):
    pin_val = pin_code or pin or kwargs.get("pin_code") or kwargs.get("pin")
    connected, devices = is_mobile_connected()
    if not connected:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected. Please connect your mobile first."}
    try:
        # Wake screen up (KEYCODE_WAKEUP 224 does not turn off if screen is already on)
        run_adb_shell("input keyevent 224")
        time.sleep(0.4)
        # Swipe up to open PIN pad or unlock swipe screen
        run_adb_shell("input swipe 360 1400 360 400 300")
        time.sleep(0.5)
        if pin_val:
            pin_str = str(pin_val).strip()
            run_adb_shell(f"input text {pin_str}")
            time.sleep(0.3)
            run_adb_shell("input keyevent 66") # KEYCODE_ENTER
        return {"status": "success", "action": "unlock_device", "message": "Device unlocked successfully."}
    except Exception as e:
        return {"status": "error", "code": "UNLOCK_FAILED", "message": str(e)}


def lock_device(**kwargs):
    connected, devices = is_mobile_connected()
    if not connected:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected."}
    try:
        run_adb_shell("input keyevent 26") # KEYCODE_POWER locks screen
        return {"status": "success", "action": "lock_device", "message": "Mobile screen locked."}
    except Exception as e:
        return {"status": "error", "code": "LOCK_FAILED", "message": str(e)}


def tap(x, y, **kwargs):
    connected, devices = is_mobile_connected()
    if not connected:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected."}
    try:
        run_adb_shell(f"input tap {x} {y}")
        return {"status": "success", "action": "tap", "message": f"Tapped at ({x}, {y})"}
    except Exception as e:
        return {"status": "error", "code": "TAP_FAILED", "message": str(e)}


def Type(text, **kwargs):
    connected, devices = is_mobile_connected()
    if not connected:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected."}
    try:
        formatted_text = str(text).replace(" ", "%s")
        run_adb_shell(f"input text {formatted_text}")
        return {"status": "success", "action": "type", "message": f"Typed text: {text}"}
    except Exception as e:
        return {"status": "error", "code": "TYPE_FAILED", "message": str(e)}


# ---------------- Phone Call ----------------
def phone_call_with_mobile(phone_number=None, number=None, **kwargs):
    target_num = phone_number or number or kwargs.get("phone_number") or kwargs.get("number") or kwargs.get("phone")
    if not target_num:
        return {"status": "error", "code": "NUMBER_REQUIRED", "message": "Phone number required for call."}
    connected, devices = is_mobile_connected()
    if not connected:
        return {
            "status": "error",
            "code": "NO_DEVICE",
            "message": "No mobile device connected. Please connect your mobile first."
        }

    try:
        target_num = str(target_num).strip()
        cleaned_num = re.sub(r"[^\d+]", "", target_num)

        if len(re.sub(r"[^\d]", "", cleaned_num)) < 3:
            return {
                "status": "error",
                "code": "INVALID_NUMBER",
                "message": "Invalid phone number provided."
            }

        # Wake screen
        run_adb_shell("input keyevent 224")
        time.sleep(0.3)

        # Make call using CALL intent
        out = run_adb_shell(f'am start -a android.intent.action.CALL -d "tel:{cleaned_num}"')

        # Fallback to DIAL if CALL intent is blocked by security permissions
        if "SecurityException" in out or "Permission" in out or "Error" in out:
            run_adb_shell(f'am start -a android.intent.action.DIAL -d "tel:{cleaned_num}"')
            time.sleep(1)
            run_adb_shell("input keyevent 5") # KEYCODE_CALL

        return {
            "status": "success",
            "action": "phone_call",
            "message": f"Calling {cleaned_num} on mobile.",
            "number": cleaned_num
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "CALL_FAILED",
            "message": str(e)
        }


def end_phone_call(**kwargs):
    connected, devices = is_mobile_connected()
    if not connected:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected."}
    try:
        run_adb_shell("input keyevent 6") # KEYCODE_ENDCALL
        return {"status": "success", "action": "end_phone_call", "message": "Call ended successfully."}
    except Exception as e:
        return {"status": "error", "code": "END_CALL_FAILED", "message": str(e)}


# ---------------- YouTube ----------------
def youtube_with_mobile(query, **kwargs):
    connected, devices = is_mobile_connected()
    if not connected:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected."}
    try:
        run_adb_shell("input keyevent 224")
        query_url = quote(str(query).replace(" ", "+"))
        run_adb_shell(f'am start -a android.intent.action.VIEW -d "https://www.youtube.com/results?search_query={query_url}"')
        time.sleep(2.5)
        # Tap first search result
        run_adb_shell("input tap 360 600")
        return {"status": "success", "action": "youtube_play", "message": f"Playing {query} on mobile", "query": str(query)}
    except Exception as e:
        return {"status": "error", "code": "YT_FAILED", "message": str(e)}


# ---------------- Google Search ----------------
def google_search_with_mobile(query, **kwargs):
    connected, devices = is_mobile_connected()
    if not connected:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected."}
    try:
        run_adb_shell("input keyevent 224")
        query_url = quote(str(query).replace(" ", "+"))
        run_adb_shell(f'am start -a android.intent.action.VIEW -d "https://www.google.com/search?q={query_url}"')
        return {"status": "success", "action": "google_search", "message": f"Searched {query} on mobile", "query": str(query)}
    except Exception as e:
        return {"status": "error", "code": "GOOGLE_SEARCH_FAILED", "message": str(e)}


# ---------------- WhatsApp Message ----------------
def send_whatsapp_message(phone_number=None, message=None, **kwargs):
    target_num = phone_number or kwargs.get("phone_number") or kwargs.get("phone") or kwargs.get("number")
    target_msg = message or kwargs.get("message") or kwargs.get("msg") or kwargs.get("text")
    if not target_num:
        return {"status": "error", "code": "NUMBER_REQUIRED", "message": "Phone number required for WhatsApp."}
    if not target_msg:
        return {"status": "error", "code": "MESSAGE_REQUIRED", "message": "Message text required for WhatsApp."}
    connected, devices = is_mobile_connected()
    if not connected:
        return {
            "status": "error",
            "code": "NO_DEVICE",
            "message": "No mobile device connected. Please connect your mobile phone first."
        }

    try:
        target_num = str(target_num).strip()
        digits = re.sub(r"[^\d]", "", target_num)

        if len(digits) < 7:
            return {
                "status": "error",
                "code": "INVALID_NUMBER",
                "message": "Invalid phone number."
            }

        # If 10 digits (standard Indian mobile number without country code), default to country code 91
        if len(digits) == 10:
            full_num = "91" + digits
        else:
            full_num = digits

        # Wake phone screen
        run_adb_shell("input keyevent 224")
        time.sleep(0.3)

        # Encode message
        encoded_msg = quote(str(target_msg))

        # Open WhatsApp chat directly
        run_adb_shell(f'am start -a android.intent.action.VIEW -d "https://api.whatsapp.com/send?phone={full_num}^&text={encoded_msg}" -p com.whatsapp')
        time.sleep(2.5)

        # Send triggers:
        # 1. KEYCODE_ENTER (66)
        run_adb_shell("input keyevent 66")
        time.sleep(0.3)
        # 2. DPAD_RIGHT (22) + ENTER (66)
        run_adb_shell("input keyevent 22")
        time.sleep(0.2)
        run_adb_shell("input keyevent 66")
        # 3. Tap Send button position (bottom-right: X=665, Y=1520 on 720x1600)
        time.sleep(0.3)
        run_adb_shell("input tap 665 1520")

        return {
            "status": "success",
            "action": "send_whatsapp",
            "message": f"WhatsApp message sent to {full_num}.",
            "text": str(target_msg)
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "WHATSAPP_FAILED",
            "message": str(e)
        }


if __name__ == "__main__":
    status = check_connection_json()
    print("Mobile Status:", status)
