import os
import sys
import time
import subprocess
import json
import threading
from datetime import datetime
from urllib.parse import quote
import re

ADB_PATH = "adb" 
ADB_PORT = "5555"

# Tracks active device serial or IP:PORT
ACTIVE_DEVICE = None

# Device Cache File Path
try:
    from utils.paths import DB_PATH
    DEVICE_CACHE_FILE = os.path.join(DB_PATH, "device_cache.json")
except Exception:
    DEVICE_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "device_cache.json")

_cache_lock = threading.Lock()

# Background Keep-Alive Daemon State
_keepalive_thread = None
_keepalive_stop_event = threading.Event()
_keepalive_lock = threading.Lock()
_consecutive_ping_failures = 0


# ---------------- Persistent Device Cache ----------------
def load_device_cache():
    """Reads cached wireless ADB device info from disk."""
    with _cache_lock:
        if not os.path.exists(DEVICE_CACHE_FILE):
            return None
        try:
            with open(DEVICE_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and data.get("ip"):
                    return data
        except Exception as e:
            print(f"[CACHE ERROR] Failed reading device cache: {e}")
        return None


def save_device_cache(ip, port="5555", pairing_port=None, extra=None):
    """Persists last successfully connected device endpoint to disk."""
    with _cache_lock:
        try:
            os.makedirs(os.path.dirname(DEVICE_CACHE_FILE), exist_ok=True)
            clean_ip = str(ip).strip()
            clean_port = str(port or ADB_PORT).strip()
            cache_data = {
                "ip": clean_ip,
                "port": clean_port,
                "pairing_port": str(pairing_port).strip() if pairing_port else None,
                "endpoint": f"{clean_ip}:{clean_port}",
                "last_connected": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            if extra and isinstance(extra, dict):
                cache_data.update(extra)
            with open(DEVICE_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=4)
            print(f"💾 [DEVICE CACHE] Saved wireless device: {cache_data['endpoint']}")
            return True
        except Exception as e:
            print(f"[CACHE ERROR] Failed saving device cache: {e}")
            return False


# ---------------- Mobile Connection & Device Resolution ----------------
def is_mobile_connected():
    """Returns (True, [device_list]) if any device is connected and authorized."""
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            [ADB_PATH, "devices"],
            capture_output=True,
            text=True,
            timeout=8,
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


def ensure_mobile_connected(auto_reconnect=True):
    """
    Ensures that a mobile device is connected.
    If disconnected, attempts to auto-reconnect using cached credentials.
    Returns (connected_bool, device_list).
    """
    global ACTIVE_DEVICE
    connected, devices = is_mobile_connected()
    if connected:
        return True, devices

    if not auto_reconnect:
        return False, []

    # Attempt recovery from persistent cache
    cache = load_device_cache()
    if not cache or not cache.get("ip"):
        return False, []

    cached_ip = cache.get("ip")
    cached_port = cache.get("port", ADB_PORT)
    endpoint = f"{cached_ip}:{cached_port}"

    print(f"🔄 [AUTO-RECONNECT] Attempting reconnection to cached device {endpoint}...")
    try:
        # Use low-level subprocess to guarantee zero recursive calls to get_target_device
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        subprocess.run(
            [ADB_PATH, "connect", endpoint],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=creation_flags
        )
        time.sleep(0.3)
        connected, devices = is_mobile_connected()
        if (endpoint in devices) or (connected and any(cached_ip in d for d in devices)):
            ACTIVE_DEVICE = endpoint if endpoint in devices else devices[0]
            print(f"✅ [AUTO-RECONNECT] Successfully reconnected to {ACTIVE_DEVICE}!")
            return True, devices
    except Exception as e:
        print(f"⚠️ [AUTO-RECONNECT] Reconnect failed: {e}")

    return False, []


def get_target_device():
    """
    Resolves the target ADB device serial or IP:PORT from currently connected devices.
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


def run_cmd(command, timeout=15):
    """
    Executes a shell command. Automatically injects -s <target_device>
    only if calling ADB shell or tcpip without -s.
    Includes timeout to prevent socket hangs during network drops.
    """
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    cmd_str = command.strip()

    # Automatically add -s <target> ONLY when executing shell or tcpip commands without -s
    if "-s " not in cmd_str and (" shell " in cmd_str or cmd_str.startswith(f"{ADB_PATH} shell") or cmd_str.startswith("adb shell") or " tcpip " in cmd_str):
        target = ACTIVE_DEVICE or get_target_device()
        if target:
            if cmd_str.startswith(f"{ADB_PATH} shell"):
                cmd_str = cmd_str.replace(f"{ADB_PATH} shell", f'"{ADB_PATH}" -s {target} shell', 1)
            elif cmd_str.startswith("adb shell"):
                cmd_str = cmd_str.replace("adb shell", f'"{ADB_PATH}" -s {target} shell', 1)
            elif cmd_str.startswith(f"{ADB_PATH} tcpip"):
                cmd_str = cmd_str.replace(f"{ADB_PATH} tcpip", f'"{ADB_PATH}" -s {target} tcpip', 1)
            elif cmd_str.startswith("adb tcpip"):
                cmd_str = cmd_str.replace("adb tcpip", f'"{ADB_PATH}" -s {target} tcpip', 1)

    try:
        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=creation_flags
        )
        if result.returncode != 0:
            err = (result.stderr or "").strip()
            if err:
                print(f"[ADB CMD ERROR] {cmd_str} -> {err}")
        return (result.stdout or "").strip()
    except subprocess.TimeoutExpired:
        print(f"[ADB CMD TIMEOUT] {cmd_str} timed out after {timeout}s")
        return ""
    except Exception as e:
        print(f"[ADB CMD EXCEPTION] {cmd_str} -> {e}")
        return ""


def run_adb_shell(subcommand, device=None, timeout=10):
    """Executes an adb shell command on the target device using -s <device>."""
    target = device or get_target_device()
    if target:
        cmd = f'"{ADB_PATH}" -s {target} shell {subcommand}'
    else:
        cmd = f'"{ADB_PATH}" shell {subcommand}'
    return run_cmd(cmd, timeout=timeout)


def check_connection_json(**kwargs):
    """Returns comprehensive JSON status of mobile ADB connection and keepalive daemon."""
    connected, devices = is_mobile_connected()
    if not connected and kwargs.get("auto_reconnect", False):
        connected, devices = ensure_mobile_connected()
    target = get_target_device()
    cache = load_device_cache()
    keepalive_active = is_keepalive_running()
    if connected:
        return {
            "status": "success",
            "message": f"Mobile connected ({target or ', '.join(devices)})",
            "devices": devices,
            "active_device": target,
            "keepalive_daemon": "active" if keepalive_active else "inactive",
            "cached_endpoint": cache.get("endpoint") if cache else None
        }
    else:
        return {
            "status": "error",
            "code": "NO_DEVICE",
            "message": "No mobile device connected. Please connect phone via USB or Wireless ADB, or use pair_mobile_device for Android 11+.",
            "keepalive_daemon": "active" if keepalive_active else "inactive",
            "cached_endpoint": cache.get("endpoint") if cache else None
        }


# ---------------- Background Heartbeat & Keep-Alive Daemon ----------------
def _adb_keepalive_worker(interval=35):
    """
    Background worker thread running every `interval` seconds (default 35s):
    1. Sends ultra-low overhead ping ('adb shell echo 1') to prevent Android Doze mode socket freeze.
    2. If connection is lost or unresponsive, automatically attempts silent
       auto-reconnection to the cached mobile device endpoint.
    """
    global _consecutive_ping_failures, ACTIVE_DEVICE
    print(f"💓 [Mobile Keep-Alive Daemon] Active. Ping interval: {interval}s.")

    while not _keepalive_stop_event.is_set():
        try:
            connected, devices = is_mobile_connected()

            if connected and devices:
                target = get_target_device()
                # Send low-overhead ping to reset kernel socket inactivity timer
                ping_cmd = f'"{ADB_PATH}" -s {target} shell echo 1' if target else f'"{ADB_PATH}" shell echo 1'
                ping_res = run_cmd(ping_cmd, timeout=5)

                if ping_res == "1":
                    _consecutive_ping_failures = 0
                else:
                    _consecutive_ping_failures += 1
                    # If ping failed or timed out, socket dropped in Doze mode
                    if _consecutive_ping_failures >= 2:
                        print(f"⚠️ [Mobile Keep-Alive] Ping dropped ({ping_res or 'timeout'}). Initiating auto-reconnect...")
                        ensure_mobile_connected(auto_reconnect=True)
            else:
                # Disconnected state: attempt background auto-reconnect if cache exists
                cache = load_device_cache()
                if cache and cache.get("ip"):
                    reconnected, _ = ensure_mobile_connected(auto_reconnect=True)
                    if not reconnected:
                        # Back off interval to 180s when device is unreachable to avoid terminal noise
                        _keepalive_stop_event.wait(180)
                        continue

        except Exception as e:
            # Resilient daemon worker, never crash
            pass

        # Wait for next ping interval or until stopped
        _keepalive_stop_event.wait(interval)

    print("🛑 [Mobile Keep-Alive Daemon] Stopped.")


def start_mobile_keepalive_daemon(interval=35):
    """Starts the background ADB heartbeat & auto-reconnect daemon thread."""
    global _keepalive_thread
    with _keepalive_lock:
        if _keepalive_thread is not None and _keepalive_thread.is_alive():
            return True
        _keepalive_stop_event.clear()
        _keepalive_thread = threading.Thread(
            target=_adb_keepalive_worker,
            args=(interval,),
            daemon=True,
            name="ADB-KeepAlive-Worker"
        )
        _keepalive_thread.start()
        return True


def stop_mobile_keepalive_daemon():
    """Stops the background ADB heartbeat daemon."""
    global _keepalive_thread
    with _keepalive_lock:
        if _keepalive_thread and _keepalive_thread.is_alive():
            _keepalive_stop_event.set()
            _keepalive_thread.join(timeout=2)
            _keepalive_thread = None
            return True
        return False


def is_keepalive_running():
    """Returns True if the keepalive worker is currently running."""
    return _keepalive_thread is not None and _keepalive_thread.is_alive()


# ---------------- Android 11+ Wireless Pairing ----------------
def pair_mobile_device(ip=None, pairing_port=None, pairing_code=None, connect_port=None, **kwargs):
    """
    Android 11+ One-Click Pairing Helper Function.
    Executes 'adb pair <ip>:<pairing_port> <pairing_code>',
    and upon successful pairing, automatically establishes connection
    to the device on the standard or specified port, saves credentials to cache,
    and starts the background keep-alive daemon.

    Parameters:
    - ip: Mobile Wi-Fi IP address (e.g. '192.168.1.5' or '192.168.1.5:38475')
    - pairing_port: 5-digit dynamic pairing port from Wireless Debugging > Pair screen
    - pairing_code: 6-digit Wi-Fi pairing code
    - connect_port: Optional connection port (defaults to 5555, or pairing_port if configured)
    """
    global ACTIVE_DEVICE

    # Resolve arguments with aliases
    target_ip = ip or kwargs.get("device_ip") or kwargs.get("ip_address") or kwargs.get("host")
    pair_port = pairing_port or kwargs.get("pair_port") or kwargs.get("port")
    code = pairing_code or kwargs.get("code") or kwargs.get("pin") or kwargs.get("pairing_pin")
    conn_port = connect_port or kwargs.get("connection_port") or ADB_PORT

    if not target_ip:
        # Check if cached IP exists
        cache = load_device_cache()
        if cache and cache.get("ip"):
            target_ip = cache.get("ip")

    if not target_ip:
        return {
            "status": "error",
            "code": "IP_REQUIRED",
            "message": "Phone Wi-Fi IP address is required (e.g., 192.168.1.5). Check Wireless Debugging in Developer Options."
        }

    target_ip = str(target_ip).strip()
    # Check if target_ip has port embedded (e.g. 192.168.1.5:38475)
    if ":" in target_ip:
        parts = target_ip.split(":")
        target_ip = parts[0].strip()
        if not pair_port and len(parts) > 1 and parts[1].strip():
            pair_port = parts[1].strip()

    if not pair_port:
        return {
            "status": "error",
            "code": "PAIRING_PORT_REQUIRED",
            "message": "Pairing port required. In Android Developer Options -> Wireless Debugging -> 'Pair device with pairing code', look for the 5-digit port (e.g., 38475)."
        }

    if not code:
        return {
            "status": "error",
            "code": "PAIRING_CODE_REQUIRED",
            "message": "6-digit pairing code required. In Android Developer Options -> Wireless Debugging -> 'Pair device with pairing code', note the 6-digit code."
        }

    pair_port = str(pair_port).strip()
    code = str(code).strip()
    pairing_endpoint = f"{target_ip}:{pair_port}"

    print(f"🔗 [ANDROID 11+ PAIRING] Pairing with {pairing_endpoint} using code {code}...")

    # Execute adb pair <ip>:<pairing_port> <pairing_code>
    pair_cmd = f'"{ADB_PATH}" pair {pairing_endpoint} {code}'
    pair_output = run_cmd(pair_cmd, timeout=12)
    print(f"ADB Pair Output: {pair_output}")

    pair_lower = pair_output.lower()
    pair_success = ("successfully paired" in pair_lower) or ("already paired" in pair_lower)

    if not pair_success:
        return {
            "status": "error",
            "code": "PAIRING_FAILED",
            "message": f"Failed to pair with {pairing_endpoint}. ADB Output: '{pair_output}'. Please verify that the 6-digit code and pairing port are still active on your phone screen."
        }

    print(f"✅ Successfully paired to {pairing_endpoint}! Establishing connection...")

    # After pairing, Android 11+ wireless debugging allows connection
    connect_result = connect_mobile_with_bat(ip_address=target_ip, port=conn_port)

    # If connection on default port fails, save cache and return guidance
    if connect_result.get("status") != "success":
        save_device_cache(ip=target_ip, port=conn_port, pairing_port=pair_port)
        return {
            "status": "partial_success",
            "action": "pair_mobile_device",
            "device_ip": target_ip,
            "pairing_port": pair_port,
            "message": f"Successfully paired with {target_ip}:{pair_port}! However, connecting to port {conn_port} returned: {connect_result.get('message')}. Please check the main Wireless Debugging screen for the active connection port."
        }

    save_device_cache(ip=target_ip, port=conn_port, pairing_port=pair_port)
    start_mobile_keepalive_daemon()

    return {
        "status": "success",
        "action": "pair_mobile_device",
        "device_ip": target_ip,
        "pairing_port": pair_port,
        "connect_port": conn_port,
        "message": f"Successfully paired with Android 11+ mobile ({pairing_endpoint}) and connected to {target_ip}:{conn_port}. Heartbeat keep-alive daemon is active!"
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
            route_out = run_cmd(f'"{ADB_PATH}" {usb_flag}shell ip route', timeout=5)
            match = re.search(r'src\s+(\d+\.\d+\.\d+\.\d+)', route_out)
            if match:
                target_ip = match.group(1)
        except Exception:
            pass

    # If still no IP, check if cached device info exists
    if not target_ip:
        cache = load_device_cache()
        if cache and cache.get("ip"):
            target_ip = cache.get("ip")
            if not kwargs.get("port") and cache.get("port"):
                kwargs["port"] = cache.get("port")

    if not target_ip:
        return {
            "status": "error",
            "code": "IP_REQUIRED",
            "message": "Mobile IP address required. Please specify your phone's Wi-Fi IP address (e.g., 192.168.1.3)."
        }

    target_ip = str(target_ip).strip()
    port = kwargs.get("port") or ADB_PORT
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
    run_cmd(f'"{ADB_PATH}" {usb_flag}tcpip {port}', timeout=6)
    time.sleep(1)

    # 🔌 Disconnect any stale session for this endpoint
    run_cmd(f'"{ADB_PATH}" disconnect {target_endpoint}', timeout=5)
    time.sleep(0.5)

    # 🚀 Connect device
    print(f"🚀 Connecting to {target_endpoint} ...")
    output = run_cmd(f'"{ADB_PATH}" connect {target_endpoint}', timeout=8)
    print(f"ADB output: {output}")

    # Check connection
    connected, devices = is_mobile_connected()
    is_success = (target_endpoint in devices) or (connected and any(target_ip in d for d in devices))

    if not is_success:
        print("🔄 Retrying connection with fresh ADB server...")
        run_cmd(f'"{ADB_PATH}" kill-server', timeout=5)
        time.sleep(1)
        run_cmd(f'"{ADB_PATH}" start-server', timeout=5)
        time.sleep(1)
        output = run_cmd(f'"{ADB_PATH}" connect {target_endpoint}', timeout=8)
        connected, devices = is_mobile_connected()
        is_success = (target_endpoint in devices) or (connected and any(target_ip in d for d in devices))

    if is_success:
        ACTIVE_DEVICE = target_endpoint if target_endpoint in devices else devices[0]
        # Save to persistent target cache
        save_device_cache(ip=target_ip, port=port)
        # Start keep-alive daemon
        start_mobile_keepalive_daemon()
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
    connected, devices = ensure_mobile_connected()
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
    connected, devices = ensure_mobile_connected()
    if not connected:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected."}
    try:
        run_adb_shell("input keyevent 26") # KEYCODE_POWER locks screen
        return {"status": "success", "action": "lock_device", "message": "Mobile screen locked."}
    except Exception as e:
        return {"status": "error", "code": "LOCK_FAILED", "message": str(e)}


def tap(x, y, **kwargs):
    connected, devices = ensure_mobile_connected()
    if not connected:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected."}
    try:
        run_adb_shell(f"input tap {x} {y}")
        return {"status": "success", "action": "tap", "message": f"Tapped at ({x}, {y})"}
    except Exception as e:
        return {"status": "error", "code": "TAP_FAILED", "message": str(e)}


def Type(text, **kwargs):
    connected, devices = ensure_mobile_connected()
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
    connected, devices = ensure_mobile_connected()
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
    connected, devices = ensure_mobile_connected()
    if not connected:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected."}
    try:
        run_adb_shell("input keyevent 6") # KEYCODE_ENDCALL
        return {"status": "success", "action": "end_phone_call", "message": "Call ended successfully."}
    except Exception as e:
        return {"status": "error", "code": "END_CALL_FAILED", "message": str(e)}


# ---------------- YouTube ----------------
def youtube_with_mobile(query, **kwargs):
    connected, devices = ensure_mobile_connected()
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
    connected, devices = ensure_mobile_connected()
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
    connected, devices = ensure_mobile_connected()
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
