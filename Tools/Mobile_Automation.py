import os
import time
import subprocess
from urllib.parse import quote
import re
from urllib.parse import quote


ADB_PATH = "adb" 
ADB_PORT = "5555"

def run_cmd(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def connect_mobile_with_bat(device_ip):
    if not device_ip:
        print("❌ IP Address required!")
        return

    print(f"📱 Device IP: {device_ip}")

    # 🔁 Restart ADB Server
    print("🔄 Restarting ADB server...")
    print(run_cmd(f"{ADB_PATH} kill-server"))
    print(run_cmd(f"{ADB_PATH} start-server"))

    # 📡 Enable TCPIP Mode
    print("📡 Switching to TCPIP mode...")
    print(run_cmd(f"{ADB_PATH} tcpip {ADB_PORT}"))

    print("⏳ Waiting for device...")
    time.sleep(3)

    # 🔌 Disconnect old connections
    print("🔌 Disconnecting old connections...")
    print(run_cmd(f"{ADB_PATH} disconnect"))

    # ✅ Connect device
    print(f"🚀 Connecting to {device_ip}:{ADB_PORT} ...")
    output = run_cmd(f"{ADB_PATH} connect {device_ip}:{ADB_PORT}")
    print(output)

    if "connected" in output.lower():
        return {"status": "success", "message": f"Connected to {device_ip}:{ADB_PORT}"}
    else:
        return {"status": "error", "message": "Connection failed!"}


# ---------------- Mobile Connection Check ----------------
def is_mobile_connected():
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        devices = [line for line in lines[1:] if line.strip() and "device" in line]

        if len(devices) > 0:
            return True, devices
        else:
            return False, []
    except:
        return False, []
    

def check_connection_json():
    connected, devices = is_mobile_connected()
    if connected:
        return {"status": "success", "message": "Mobile connected", "devices": devices}
    else:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected"}
    


# ---------------- Mobile Controls ----------------
def unlock_device(pin_code):
    if not is_mobile_connected()[0]:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected"}
    try:
        subprocess.run(["adb", "shell", "input", "keyevent", "26"])
        time.sleep(1)
        subprocess.run(["adb", "shell", "input", "swipe", "500", "1500", "500", "500"])
        time.sleep(1)
        subprocess.run(["adb", "shell", "input", "text", pin_code])
        time.sleep(1)
        subprocess.run(["adb", "shell", "input", "keyevent", "66"])
        return {"status": "success", "action": "unlock_device", "message": "Device unlocked"}
    except Exception as e:
        return {"status": "error", "code": "UNLOCK_FAILED", "message": str(e)}
    

def tap(x, y):
    if not is_mobile_connected()[0]:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected"}
    try:
        os.system(f"adb shell input tap {x} {y}")
        return {"status": "success", "action": "tap", "message": f"Tapped at ({x}, {y})"}
    except Exception as e:
        return {"status": "error", "code": "TAP_FAILED", "message": str(e)}


def Type(text):
    if not is_mobile_connected()[0]:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected"}
    try:
        formatted_text = text.replace(" ", "%s")
        os.system(f"adb shell input text {formatted_text}")
        return {"status": "success", "action": "type", "message": f"Typed text: {text}"}
    except Exception as e:
        return {"status": "error", "code": "TYPE_FAILED", "message": str(e)}



# ---------------- Phone Call ----------------

def phone_call_with_mobile(phone_number):
    if not is_mobile_connected()[0]:
        return {
            "status": "error",
            "code": "NO_DEVICE",
            "message": "No mobile device connected"
        }

    try:
        # ✅ Clean number (remove spaces, +, - etc)
        phone_number = str(phone_number).strip()
        phone_number = re.sub(r"[^\d]", "", phone_number)

        if len(phone_number) < 8:
            return {
                "status": "error",
                "code": "INVALID_NUMBER",
                "message": "Invalid phone number provided"
            }

        # 📞 Make call using ADB
        os.system(
            f'adb shell am start -a android.intent.action.CALL -d tel:{phone_number}'
        )

        return {
            "status": "success",
            "action": "phone_call",
            "message": f"Calling {phone_number}",
            "number": phone_number
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "CALL_FAILED",
            "message": str(e)
        }


# ---------------- YouTube ----------------
def youtube_with_mobile(query):
    if not is_mobile_connected()[0]:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected"}
    try:
        query_url = quote(query.replace(" ", "+"))
        os.system(f'adb shell am start -a android.intent.action.VIEW -d "https://www.youtube.com/results?search_query={query_url}"')
        time.sleep(2)
        os.system('adb shell input tap 454 754')
        return {"status": "success", "action": "youtube_play", "message": f"Playing {query}", "query": query}
    except Exception as e:
        return {"status": "error", "code": "YT_FAILED", "message": str(e)}



# ---------------- Google Search ----------------
def google_search_with_mobile(query):
    if not is_mobile_connected()[0]:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected"}
    try:
        query_url = quote(query.replace(" ", "+"))
        os.system(f'adb shell am start -a android.intent.action.VIEW -d "https://www.google.com/search?q={query_url}"')
        return {"status": "success", "action": "google_search", "message": f"Searched {query}", "query": query}
    except Exception as e:
        return {"status": "error", "code": "GOOGLE_SEARCH_FAILED", "message": str(e)}



# ---------------- WhatsApp Message ----------------

def send_whatsapp_message(phone_number, message):
    if not is_mobile_connected()[0]:
        return {
            "status": "error",
            "code": "NO_DEVICE",
            "message": "No mobile device connected"
        }

    try:
        # ✅ Clean phone number
        phone_number = str(phone_number).strip()
        phone_number = re.sub(r"[^\d]", "", phone_number)

        if len(phone_number) < 8:
            return {
                "status": "error",
                "code": "INVALID_NUMBER",
                "message": "Invalid phone number"
            }

        # ✅ Encode message safely
        final_msg = quote(message)

        # 📩 Open WhatsApp chat
        os.system(
            f'adb shell am start -a android.intent.action.VIEW '
            f'-d "https://wa.me/{phone_number}?text={final_msg}"'
        )

        time.sleep(2)

        # 📤 Press Enter to Send
        os.system('adb shell input keyevent KEYCODE_ENTER')

        # 🧹 Optional: close WhatsApp
        os.system('adb shell am force-stop com.whatsapp')

        return {
            "status": "success",
            "action": "send_whatsapp",
            "message": f"Message sent to {phone_number}",
            "text": message
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "WHATSAPP_FAILED",
            "message": str(e)
        }

# 👉 run
if __name__ == "__main__":
    ip = input("Enter Device IP: ")
    google_search_with_mobile("F.R.I.D.A.Y AI Assistant")
    # connect_mobile_with_bat(ip)
