import threading
import time
import speech_recognition as sr

# Expanded list of trigger phrases and common phonetic misrecognitions by STT
DEFAULT_KEYWORDS = [
    "friday", "hey friday", "ok friday", "okay friday", "hello friday", "hi friday",
    "listen friday", "yo friday",
    # Phonetic variants commonly returned by Google STT
    "fry day", "hey fry day", "ok fry day", "freeday", "hey freeday",
    "fraiday", "hey fraiday", "frida", "hey frida", "fridey", "phriday"
]

TARGET_WORDS = {"friday", "fryday", "freeday", "fraiday", "frida", "fridey", "phriday"}


class WakeWordListener:
    """
    Robust background listener for 'Friday' / 'Hey Friday' wake-word activation.
    Uses continuous background audio streaming via SpeechRecognition to avoid
    device open/close glitches and dropped audio packets on Windows.
    """

    def __init__(self, keywords=None, on_wake_word=None):
        self.keywords = [k.lower().strip() for k in (keywords or DEFAULT_KEYWORDS)]
        self.on_wake_word = on_wake_word
        self._running = False
        self._stop_listening = None
        self._triggered = threading.Event()
        self.last_detected_text = ""
        self.recognizer = None
        self.mic = None

    def _matches_keyword(self, text: str) -> bool:
        if not text:
            return False
        clean = text.lower().strip()
        # Direct substring match
        for kw in self.keywords:
            if kw in clean:
                return True
        # Word-level check for phonetic variants
        words = [w.strip(".,!?\"' ") for w in clean.split()]
        if any(w in TARGET_WORDS for w in words):
            return True
        return False

    def _audio_callback(self, recognizer, audio):
        """Executed in background thread whenever a phrase is captured."""
        if not self._running:
            return
        try:
            # Fast Google Speech Recognition check
            text = recognizer.recognize_google(audio).lower().strip()
            if self._matches_keyword(text):
                has_wake, command = self.extract_command(text)
                self.last_detected_text = text
                self._triggered.set()
                if self.on_wake_word:
                    try:
                        # Try 2-arg callback (phrase, command) first
                        self.on_wake_word(text, command)
                    except TypeError:
                        # Fallback to 1-arg callback for backward compatibility
                        try:
                            self.on_wake_word(text)
                        except Exception:
                            pass
                    except Exception:
                        pass
        except (sr.UnknownValueError, sr.RequestError):
            pass
        except Exception:
            pass

    def extract_command(self, text: str = None):
        """
        Extracts the command part from a phrase that contains the wake word.
        Returns (has_wake_word: bool, command_text: str).
        E.g.
        'friday what is the weather' -> (True, 'what is the weather')
        'hey friday open chrome'     -> (True, 'open chrome')
        'friday'                     -> (True, '')
        'hey friday'                 -> (True, '')
        """
        raw = (text if text is not None else self.last_detected_text) or ""
        clean = raw.lower().strip()
        if not self._matches_keyword(clean):
            return False, ""

        sorted_keywords = sorted(self.keywords, key=len, reverse=True)
        extracted = clean
        for kw in sorted_keywords:
            if kw in extracted:
                extracted = extracted.replace(kw, " ", 1)
                break
        else:
            words = extracted.split()
            filtered = [w for w in words if w.strip(".,!?\"' ") not in TARGET_WORDS]
            extracted = " ".join(filtered)

        extracted = extracted.strip(" ,.:-!?\"'")
        # Strip common leading conversational prefixes
        for prefix in ["hey", "hello", "hi", "ok", "okay", "please", "can you", "batao", "bataiye"]:
            if extracted.startswith(prefix + " "):
                extracted = extracted[len(prefix):].strip(" ,.:-!?\"'")

        return True, extracted

    def start(self) -> bool:
        """Start listening for the wake word in the background."""
        if self._running:
            return True

        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.dynamic_energy_adjustment_damping = 0.15
            self.recognizer.dynamic_energy_ratio = 1.5
            self.recognizer.pause_threshold = 0.5
            self.recognizer.operation_timeout = None

            self.mic = sr.Microphone()
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.6)

            self._running = True
            self._triggered.clear()
            self._stop_listening = self.recognizer.listen_in_background(
                self.mic,
                self._audio_callback,
                phrase_time_limit=7.0
            )
            return True
        except Exception:
            self._running = False
            return False

    def stop(self) -> bool:
        """Stop the background wake word listener cleanly."""
        if not self._running:
            return False
        self._running = False
        if self._stop_listening:
            try:
                self._stop_listening(wait_for_stop=False)
            except Exception:
                pass
            self._stop_listening = None
        self._triggered.clear()
        return True

    def is_running(self) -> bool:
        return self._running

    def is_triggered(self) -> bool:
        return self._triggered.is_set()

    def clear_trigger(self):
        self._triggered.clear()
        self.last_detected_text = ""


_default_listener = None


def extract_command(text: str):
    """
    Module-level helper to extract command text from a wake-word phrase.
    Returns (has_wake_word: bool, command_text: str).
    """
    global _default_listener
    if _default_listener is None:
        _default_listener = WakeWordListener()
    return _default_listener.extract_command(text)


if __name__ == "__main__":
    def on_wake(text):
        print(f"⚡ Wake word detected: '{text}'!")

    print("🎙️ Testing Wake Word Listener (Say 'Friday' or 'Hey Friday')...")
    w = WakeWordListener(on_wake_word=on_wake)
    if w.start():
        print("Listener running for 10 seconds. Say 'Friday'...")
        time.sleep(10)
        w.stop()
        print("Test complete.")
    else:
        print("Failed to start microphone listener.")
