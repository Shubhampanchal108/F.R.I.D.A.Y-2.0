import pyautogui
from datetime import time

def yt_play_pause():
    try:
        pyautogui.press("space")
        return {
            "status": "success",
            "action": "yt_play_pause",
            "message": "Toggled Play/Pause on YouTube"
        }
    except Exception as e:
        return {
            "status": "error",
            "code": "YT_PLAY_PAUSE_FAILED",
            "message": str(e)
        }

def yt_next():
    try:
        pyautogui.press("shift")  # optional, if needed with 'n' for some browsers
        pyautogui.press("n")      # YouTube next video shortcut
        return {
            "status": "success",
            "action": "yt_next",
            "message": "Skipped to next YouTube video"
        }
    except Exception as e:
        return {
            "status": "error",
            "code": "YT_NEXT_FAILED",
            "message": str(e)
        }

def yt_previous():
    try:
        pyautogui.press("p")  # YouTube previous video shortcut
        return {
            "status": "success",
            "action": "yt_previous",
            "message": "Went to previous YouTube video"
        }
    except Exception as e:
        return {
            "status": "error",
            "code": "YT_PREVIOUS_FAILED",
            "message": str(e)
        }

def yt_fullscreen():
    try:
        pyautogui.press("f")
        return {
            "status": "success",
            "action": "yt_fullscreen",
            "message": "Toggled Fullscreen on YouTube"
        }
    except Exception as e:
        return {
            "status": "error",
            "code": "YT_FULLSCREEN_FAILED",
            "message": str(e)
        }


def capture_screenshot(filename=None):
    try:
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"

        screenshot = pyautogui.screenshot()
        screenshot.save(filename)

        return {
            "status": "success",
            "action": "capture_screenshot",
            "message": "Screenshot captured",
            "filename": filename
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "SCREENSHOT_FAILED",
            "message": str(e)
        }
