# mobile_tools_json.py
import os
import time
import subprocess
from urllib.parse import quote
# from configs import contact

contact = {

}

def connect_mobile_with_bat(ip_address):
    bat_path=r"C:\Users\j\OneDrive\Desktop\shubham studio\F.R.I.D.A.Y\Database\docs\device.bat"

    try:
        result = subprocess.run([bat_path, ip_address], shell=True, capture_output=True, text=True, timeout=20)
        # Check if device connected
        devices_result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        lines = devices_result.stdout.strip().split("\n")
        devices = [line for line in lines[1:] if line.strip() and "device" in line]

        if len(devices) > 0:
            return {"status": "success", "action": "connect_mobile", "message": f"Mobile connected using IP {ip_address}", "devices": devices}
        else:
            return {"status": "error", "code": "NO_DEVICE", "message": f"Mobile not connected using IP {ip_address}"}

    except Exception as e:
        return {"status": "error", "code": "CONNECT_FAILED", "message": str(e)}
    

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
def unlock_device(pin_code="9445"):
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
def phone_call_with_mobile(contact_name):
    if not is_mobile_connected()[0]:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected"}
    try:
        contact_name = contact_name.lower()
        phone_number = contact.get(contact_name)
        if not phone_number:
            return {"status": "error", "code": "CONTACT_NOT_FOUND", "message": f"No contact named {contact_name}"}
        os.system(f'adb shell am start -a android.intent.action.CALL -d tel:{phone_number}')
        return {"status": "success", "action": "phone_call", "message": f"Calling {contact_name}", "contact": contact_name}
    except Exception as e:
        return {"status": "error", "code": "CALL_FAILED", "message": str(e)}



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
def send_whatsapp_message_mobile(contact_name, message):
    if not is_mobile_connected()[0]:
        return {"status": "error", "code": "NO_DEVICE", "message": "No mobile device connected"}
    try:
        contact_name = contact_name.lower()
        phone_number = contact.get(contact_name)
        if not phone_number:
            return {"status": "error", "code": "CONTACT_NOT_FOUND", "message": f"No contact named {contact_name}"}

        final_msg = quote(message)
        os.system(f'adb shell am start -a android.intent.action.VIEW -d "https://wa.me/{phone_number}?text={final_msg}"')
        time.sleep(2)
        os.system('adb shell input keyevent KEYCODE_ENTER')
        os.system('adb shell am force-stop com.whatsapp')
        return {"status": "success", "action": "send_whatsapp", "message": f"Message sent to {contact_name}", "text": message}
    except Exception as e:
        return {"status": "error", "code": "WHATSAPP_FAILED", "message": str(e)}


print(connect_mobile_with_bat("10.229.241.226"))