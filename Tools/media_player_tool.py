"""
F.R.I.D.A.Y // Global System Media Controller
Controls OS-level playback for Spotify, YouTube, VLC, browser audio, etc. using Windows virtual key events.
"""

import ctypes
import time

# Windows Virtual Key Codes for Hardware Media Keys
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002


def _send_vk(vk_code: int):
    """Dispatches a hardware key-down followed by key-up event."""
    user32 = ctypes.windll.user32
    user32.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


def system_media_control(action: str = "play_pause") -> dict:
    """
    Controls Windows global media playback.
    Supported actions:
    - 'play', 'pause', 'play_pause', 'toggle' -> Toggles Play/Pause across Spotify, YouTube, VLC, media players.
    - 'next', 'skip' -> Skips to the next track.
    - 'previous', 'prev', 'back' -> Returns to the previous track.
    - 'stop' -> Stops media playback.
    """
    try:
        act = str(action).lower().strip()
        if act in ["play", "pause", "play_pause", "toggle", "resume"]:
            _send_vk(VK_MEDIA_PLAY_PAUSE)
            msg = "Global media playback toggled (Play/Pause)."
        elif act in ["next", "skip", "forward"]:
            _send_vk(VK_MEDIA_NEXT_TRACK)
            msg = "Skipped to next media track."
        elif act in ["prev", "previous", "back"]:
            _send_vk(VK_MEDIA_PREV_TRACK)
            msg = "Returned to previous media track."
        elif act in ["stop"]:
            _send_vk(VK_MEDIA_STOP)
            msg = "Media playback stopped."
        else:
            return {
                "status": "error",
                "message": f"Unsupported media action: '{action}'. Available: play_pause, next, previous, stop."
            }

        return {
            "status": "success",
            "action": f"media_{act}",
            "message": msg
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Media control error: {str(e)}"
        }
