import threading
import time
import speech_recognition as sr


class WakeWordListener:
    def __init__(self, keywords=None, on_wake_word=None):
        self.keywords = keywords or ["friday", "hey friday", "ok friday"]
        self.on_wake_word = on_wake_word
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()

    def _listen_loop(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        while not self._stop_event.is_set():
            try:
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=2, phrase_time_limit=3)

                try:
                    text = recognizer.recognize_google(audio).lower().strip()
                    if any(kw in text for kw in self.keywords):
                        if self.on_wake_word:
                            self.on_wake_word(text)
                except (sr.UnknownValueError, sr.RequestError):
                    pass

            except sr.WaitTimeoutError:
                pass
            except Exception:
                time.sleep(0.5)

    def start(self):
        if self._running:
            return False
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        if not self._running:
            return False
        self._running = False
        self._stop_event.set()
        return True

    def is_running(self):
        return self._running and self._thread is not None and self._thread.is_alive()


if __name__ == "__main__":
    def on_wake(text):
        print(f"⚡ Wake word detected: '{text}'!")

    print("🎙️ Testing Wake Word Listener (Say 'Friday')...")
    w = WakeWordListener(on_wake_word=on_wake)
    w.start()
    time.sleep(5)
    w.stop()
    print("Test complete.")
