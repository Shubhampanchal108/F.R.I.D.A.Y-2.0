import os
import random
import threading
import time

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

try:
    if not pygame.mixer.get_init():
        pygame.mixer.init()
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILLERS_DIR = os.path.join(BASE_DIR, "assets", "audio", "fillers")

# Filler mapping based on query keywords
FILLER_KEYWORDS = {
    "analyzing_screen": [
        "screen", "display", "screenshot", "error", "what is on", "look at", 
        "see this", "code error", "read screen", "dekho", "kya chal raha hai", "kya hai screen par"
    ],
    "accessing_records": [
        "search", "google", "wikipedia", "find", "who is", "what is", 
        "news", "weather", "latest", "lookup", "dhoondo", "pata karo"
    ],
    "checking": [
        "battery", "cpu", "status", "remind", "reminder", "task", "todo", 
        "email", "mail", "check", "kitna hai"
    ],
    "on_it": [
        "play", "youtube", "music", "song", "open", "close", "minimize", 
        "maximize", "volume", "brightness", "chalao", "kholo", "band karo"
    ],
    "right_away": [
        "download", "run", "execute", "create", "make", "banao", "start"
    ],
    "one_moment": [
        "why", "how", "explain", "summarize", "karo", "tell me"
    ]
}

_channel = None
_last_played_time = 0


def _get_sound_channel():
    global _channel
    try:
        if _channel is None:
            _channel = pygame.mixer.Channel(1)
        return _channel
    except Exception:
        return None


def select_filler_key(query: str) -> str:
    """Intelligently matches query intent to the most appropriate filler sound."""
    q_lower = (query or "").lower().strip()

    for filler_key, keywords in FILLER_KEYWORDS.items():
        if any(kw in q_lower for kw in keywords):
            return filler_key

    # General fallback pool
    general_pool = ["on_it", "right_away", "checking", "one_moment"]
    return random.choice(general_pool)


def is_filler_busy() -> bool:
    """Returns True if the instant filler channel is actively playing audio."""
    global _channel
    try:
        return _channel is not None and _channel.get_busy()
    except Exception:
        return False


def stop_instant_filler():
    """Immediately halts any playing instant filler audio."""
    global _channel
    try:
        if _channel and _channel.get_busy():
            _channel.stop()
    except Exception:
        pass


def trigger_instant_filler(query: str, audio_enabled: bool = True) -> bool:
    """
    Plays an instant (<10ms latency) acknowledgment voice filler in a non-blocking background thread.
    Completely eliminates awkward silence while LLM processes the query.
    """
    global _last_played_time

    if not audio_enabled or not os.path.exists(FILLERS_DIR):
        return False

    # Prevent triggering filler if voice output is disabled globally or Friday is speaking
    try:
        from speak import is_speaking, is_voice_enabled
        if not is_voice_enabled() or is_speaking():
            return False
    except Exception:
        pass

    # Prevent rapid repeat triggers within 2 seconds
    now = time.time()
    if now - _last_played_time < 2.0:
        return False
    _last_played_time = now

    def _play_worker():
        try:
            filler_name = select_filler_key(query)
            audio_path = os.path.join(FILLERS_DIR, f"{filler_name}.mp3")

            if not os.path.exists(audio_path):
                # Fallback to any existing filler
                files = [f for f in os.listdir(FILLERS_DIR) if f.endswith(".mp3")]
                if not files:
                    return
                audio_path = os.path.join(FILLERS_DIR, files[0])

            channel = _get_sound_channel()
            sound = pygame.mixer.Sound(audio_path)
            sound.set_volume(0.85)

            if channel:
                channel.play(sound)
            else:
                sound.play()

        except Exception as e:
            # Non-critical sound error
            pass

    th = threading.Thread(target=_play_worker, daemon=True)
    th.start()
    return True


if __name__ == "__main__":
    print("Testing Instant Filler Responses...")
    trigger_instant_filler("look at my screen and fix this error")
    time.sleep(2)
    trigger_instant_filler("google search latest AI news")
    time.sleep(2)
    print("Instant filler test completed.")
