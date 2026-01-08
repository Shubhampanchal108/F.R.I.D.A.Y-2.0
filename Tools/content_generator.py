import subprocess
import time
import pyautogui

def write_to_notepad(content: str):
    try:
        # Open Notepad
        subprocess.Popen(["notepad.exe"])
        time.sleep(1.5)  # wait for Notepad to open

        # Type content
        pyautogui.write(content, interval=0.02)

        return {
            "status": "success",
            "message": "Content written to Notepad"
        }

    except Exception as e:
        return {
            "error": str(e)
        }