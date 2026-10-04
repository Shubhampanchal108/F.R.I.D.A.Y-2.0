import os
import queue
import threading
import time
import uuid
import warnings
from gtts import gTTS
from path import AUDIO_PATH

warnings.filterwarnings("ignore", category=UserWarning)

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Platform-specific keyboard detection
try:
    import msvcrt
except ImportError:
    msvcrt = None

try:
    import ctypes
    user32 = ctypes.windll.user32
except Exception:
    user32 = None

# Windows Virtual-Key Codes for real-time key capture
VK_CONTROL = 0x11
VK_D = 0x44
VK_ESCAPE = 0x1B

# ===============================
# INIT PYGAME AUDIO
# ===============================
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init()
except Exception:
    pass

audio_queue = queue.Queue()
STOP_SIGNAL = "STOP"

AUDIO_FOLDER = AUDIO_PATH
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Global tracking of active speech for interruption
_current_stop_event = None
_speech_lock = threading.Lock()


def is_speaking():
    """Returns True if speech is actively playing or generating."""
    global _current_stop_event
    return _current_stop_event is not None and not _current_stop_event.is_set()


def stop_speaking():
    """Stops any currently playing or queued speech immediately."""
    global _current_stop_event
    if _current_stop_event is not None and not _current_stop_event.is_set():
        _current_stop_event.set()
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
    except Exception:
        pass


def check_interrupt_key():
    """
    Checks if an interruption key (Ctrl+D, Esc, 'q', 's', etc.) has been triggered.
    Uses user32.GetAsyncKeyState for hotkeys and msvcrt for console keystrokes.
    """
    if user32:
        try:
            # Ctrl + D
            if (user32.GetAsyncKeyState(VK_CONTROL) & 0x8000) and (user32.GetAsyncKeyState(VK_D) & 0x8000):
                return True
            # Esc
            if user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000:
                return True
        except Exception:
            pass

    if msvcrt:
        try:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                # Ctrl+D is \x04, Esc is \x1b, Ctrl+C is \x03, 'q', 'Q', 's', 'S'
                if ch in (b'\x04', b'\x1b', b'\x03', b'q', b'Q', b's', b'S'):
                    return True
        except Exception:
            pass

    return False


def flush_terminal_input():
    """Flushes any remaining buffered keystrokes from the console stdin."""
    if msvcrt:
        try:
            time.sleep(0.06)
            while msvcrt.kbhit():
                msvcrt.getch()
        except Exception:
            pass


# ===============================
# Split text into chunks
# ===============================
def split_text(text, max_len=100):
    try:
        if not text:
            return []

        chunks = []
        start = 0
        i = 0
        text_len = len(text)

        while i < text_len:
            if text[i] == ".":
                chunk = text[start:i].strip()
                if chunk:
                    chunks.append(chunk)
                start = i + 1

            if i - start + 1 >= max_len:
                window = text[start:i + 1]
                cut = window.rfind(" ")
                end = start + (cut if cut != -1 else len(window))
                chunk = text[start:end].strip()
                if chunk:
                    chunks.append(chunk)
                start = end
                while start < text_len and text[start] in [" ", "."]:
                    start += 1
                i = start - 1

            i += 1

        tail = text[start:].strip()
        if tail:
            chunks.append(tail)

        return chunks
    except Exception as e:
        print("❌ Split Error:", e)
        return []


# ===============================
# Producer: create audio files
# ===============================
def audio_producer(text, session_id, audio_q, stop_event):
    try:
        chunks = split_text(text)

        if not chunks:
            audio_q.put(STOP_SIGNAL)
            return

        for index, chunk in enumerate(chunks):
            if stop_event.is_set():
                break

            try:
                filename = os.path.join(AUDIO_FOLDER, f"voice_{session_id}_{index}.mp3")

                tts = gTTS(text=chunk)
                if stop_event.is_set():
                    break

                tts.save(filename)

                if stop_event.is_set():
                    try:
                        if os.path.exists(filename):
                            os.remove(filename)
                    except Exception:
                        pass
                    break

                audio_q.put(filename)

            except Exception as e:
                if not stop_event.is_set():
                    print(f"❌ TTS Error on chunk {index}:", e)

    except Exception as e:
        if not stop_event.is_set():
            print("❌ Producer Crash:", e)

    finally:
        audio_q.put(STOP_SIGNAL)


# ===============================
# Consumer: play audio using pygame
# ===============================
def audio_consumer(audio_q, stop_event):
    try:
        while not stop_event.is_set():
            try:
                filename = audio_q.get(timeout=0.1)
            except queue.Empty:
                continue

            if filename == STOP_SIGNAL or stop_event.is_set():
                break

            try:
                if not os.path.exists(filename):
                    continue

                # ▶️ Load & play
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()

                # ⏳ Wait until playback finishes or stop requested
                while pygame.mixer.music.get_busy():
                    if stop_event.is_set():
                        pygame.mixer.music.stop()
                        break
                    time.sleep(0.03)

                # 🛑 Release file lock properly
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                time.sleep(0.05)

            except Exception as e:
                if not stop_event.is_set():
                    print("❌ Play Error:", e)

            finally:
                # 🧹 Safe delete with retry
                for _ in range(5):
                    try:
                        if os.path.exists(filename):
                            os.remove(filename)
                            break
                    except Exception:
                        time.sleep(0.05)

    except Exception as e:
        if not stop_event.is_set():
            print("❌ Consumer Crash:", e)

    finally:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass

        # Drain any residual items
        while not audio_q.empty():
            try:
                fn = audio_q.get_nowait()
                if fn != STOP_SIGNAL and os.path.exists(fn):
                    try:
                        os.remove(fn)
                    except Exception:
                        pass
            except Exception:
                break


def cleanup_session_files(session_id):
    """Deletes any residual audio files associated with this session."""
    try:
        for f in os.listdir(AUDIO_FOLDER):
            if session_id in f and f.endswith(".mp3"):
                fp = os.path.join(AUDIO_FOLDER, f)
                try:
                    os.remove(fp)
                except Exception:
                    pass
    except Exception:
        pass


def _safe_print(markup_text, fallback_text):
    try:
        from rich.console import Console
        c = Console()
        c.print(markup_text)
    except Exception:
        try:
            enc = sys.stdout.encoding or "utf-8"
            clean = fallback_text.encode(enc, errors="replace").decode(enc)
            print(clean)
        except Exception:
            pass


# ===============================
# Main speak function
# ===============================
def speak(text, allow_interrupt=True):
    """
    Main speak function with real-time keyboard interruption support.
    Users can press Ctrl+D, Esc, or 'q' at any time to immediately stop speech
    and proceed directly to their next input.
    """
    global _current_stop_event

    if not text or not str(text).strip():
        return True

    clean_text = str(text).strip()

    # Stop any lingering audio from previous calls
    stop_speaking()

    with _speech_lock:
        stop_event = threading.Event()
        _current_stop_event = stop_event
        session_id = uuid.uuid4().hex[:8]
        audio_q = queue.Queue()

        producer = threading.Thread(
            target=audio_producer,
            args=(clean_text, session_id, audio_q, stop_event),
            daemon=True
        )
        consumer = threading.Thread(
            target=audio_consumer,
            args=(audio_q, stop_event),
            daemon=True
        )

        producer.start()
        consumer.start()

        interrupted = False

        if allow_interrupt:
            _safe_print(
                "[dim cyan]🔊 Speaking... [dim white](Press [bold yellow]Ctrl+D[/bold yellow] or [bold yellow]Esc[/bold yellow] to interrupt)[/dim cyan]",
                "[Speaking... Press Ctrl+D or Esc to interrupt]"
            )

        try:
            while consumer.is_alive():
                if allow_interrupt and check_interrupt_key():
                    interrupted = True
                    stop_event.set()
                    try:
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()
                    except Exception:
                        pass
                    flush_terminal_input()
                    break

                time.sleep(0.04)

        except KeyboardInterrupt:
            interrupted = True
            stop_event.set()
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception:
                pass
            flush_terminal_input()

        finally:
            if interrupted:
                stop_event.set()
                _safe_print(
                    "\n[bold yellow]⏹️ Speech stopped (Interrupted by user). Ready for next prompt.[/bold yellow]",
                    "\n[Speech stopped. Ready for next prompt.]"
                )

            consumer.join(timeout=0.4)
            cleanup_session_files(session_id)
            _current_stop_event = None

        return not interrupted
