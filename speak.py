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

STOP_SIGNAL = "STOP"
AUDIO_FOLDER = AUDIO_PATH
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# =========================================================================
# CENTRAL THREAD-SAFE SPEECH QUEUE & INTERRUPTION MANAGER
# =========================================================================

class SpeechItem:
    """Encapsulates a speech request with priority, callbacks, and synchronization."""
    def __init__(self, text, priority=1, allow_interrupt=True, on_start=None, on_end=None, done_event=None):
        self.text = text
        self.priority = priority  # 1 = User Query, 2 = Critical Alert, 3 = Ambient Alert
        self.timestamp = time.time()
        self.allow_interrupt = allow_interrupt
        self.on_start = on_start
        self.on_end = on_end
        self.done_event = done_event
        self.interrupted = False

    def __lt__(self, other):
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.timestamp < other.timestamp


_speech_queue = queue.PriorityQueue()
_speech_lock = threading.Lock()
_current_stop_event = None
_current_item = None
_global_on_start_callbacks = []
_global_on_end_callbacks = []


def register_speech_callback(on_start=None, on_end=None):
    """Registers global callbacks for speech start and end events (used by UI widget)."""
    global _global_on_start_callbacks, _global_on_end_callbacks
    if on_start and on_start not in _global_on_start_callbacks:
        _global_on_start_callbacks.append(on_start)
    if on_end and on_end not in _global_on_end_callbacks:
        _global_on_end_callbacks.append(on_end)


def is_speaking():
    """Returns True if speech is actively generating, queued, or playing."""
    global _current_stop_event, _speech_queue
    if _current_stop_event is not None and not _current_stop_event.is_set():
        return True
    try:
        return not _speech_queue.empty()
    except Exception:
        return False


def stop_speaking():
    """
    Alias for interrupt_speech(). Immediately silences all ongoing and queued speech,
    stops instant fillers, and returns Friday to listening/standby state.
    """
    interrupt_speech()


def interrupt_speech():
    """
    Core Interruption Handler:
    1. Signals the current active TTS playback/producer to immediately stop.
    2. Stops and unloads pygame mixer music.
    3. Stops all sound channels (silences instant fillers).
    4. Flushes and clears all queued pending speech requests so backlogged audio is never spoken.
    5. Cleans up audio files and notifies UI listeners.
    """
    global _current_stop_event, _current_item, _speech_queue

    # 1. Drain pending queue items
    drained_count = 0
    while not _speech_queue.empty():
        try:
            item = _speech_queue.get_nowait()
            if item:
                item.interrupted = True
                if item.done_event:
                    item.done_event.set()
                if item.on_end:
                    try:
                        item.on_end(interrupted=True)
                    except Exception:
                        pass
                drained_count += 1
            _speech_queue.task_done()
        except Exception:
            break

    # 2. Stop currently playing speech item
    if _current_item:
        _current_item.interrupted = True

    if _current_stop_event is not None and not _current_stop_event.is_set():
        _current_stop_event.set()

    # 3. Cut off all pygame audio instantly
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
    except Exception:
        pass

    try:
        pygame.mixer.stop()  # Silences Channel(1) instant fillers as well!
    except Exception:
        pass

    # 4. Flush keyboard input
    flush_terminal_input()

    # 5. Notify listeners of speech end due to interruption
    for cb in _global_on_end_callbacks:
        try:
            cb(interrupted=True)
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
            time.sleep(0.04)
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
                    pass

    except Exception as e:
        pass

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

                # Load & play
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()

                # Wait until playback finishes or stop requested
                while pygame.mixer.music.get_busy():
                    if stop_event.is_set():
                        pygame.mixer.music.stop()
                        break
                    time.sleep(0.02)

                # Release file lock properly
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                time.sleep(0.03)

            except Exception as e:
                pass

            finally:
                # Safe delete with retry
                for _ in range(5):
                    try:
                        if os.path.exists(filename):
                            os.remove(filename)
                            break
                    except Exception:
                        time.sleep(0.04)

    except Exception as e:
        pass

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


# =========================================================================
# CENTRAL SEQUENTIAL SPEECH WORKER THREAD
# =========================================================================

def _play_speech_item(item: SpeechItem):
    """Plays an individual SpeechItem from start to finish with interruption support."""
    global _current_stop_event, _current_item

    if item.interrupted or not item.text:
        if item.done_event:
            item.done_event.set()
        return

    # Wait up to 350ms if instant filler is wrapping up so voices don't clash
    try:
        from instant_filler import is_filler_busy, stop_instant_filler
        if is_filler_busy():
            for _ in range(7):
                if not is_filler_busy():
                    break
                time.sleep(0.05)
            stop_instant_filler()
    except Exception:
        pass

    stop_event = threading.Event()
    _current_stop_event = stop_event
    _current_item = item

    session_id = uuid.uuid4().hex[:8]
    audio_q = queue.Queue()

    # Notify listeners that speech has started
    if item.on_start:
        try:
            item.on_start(item.text)
        except Exception:
            pass

    for cb in _global_on_start_callbacks:
        try:
            cb(item.text)
        except Exception:
            pass

    producer = threading.Thread(
        target=audio_producer,
        args=(item.text, session_id, audio_q, stop_event),
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

    if item.allow_interrupt:
        _safe_print(
            "[dim cyan]🔊 Speaking... [dim white](Press [bold yellow]Ctrl+D[/bold yellow] or [bold yellow]Esc[/bold yellow] to interrupt)[/dim cyan]",
            "[Speaking... Press Ctrl+D or Esc to interrupt]"
        )

    try:
        while consumer.is_alive():
            if stop_event.is_set():
                interrupted = True
                break

            if item.allow_interrupt and check_interrupt_key():
                interrupted = True
                item.interrupted = True
                stop_event.set()
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                except Exception:
                    pass
                flush_terminal_input()
                break

            time.sleep(0.03)

    except KeyboardInterrupt:
        interrupted = True
        item.interrupted = True
        stop_event.set()
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass
        flush_terminal_input()

    finally:
        if interrupted or stop_event.is_set():
            stop_event.set()
            item.interrupted = True
            _safe_print(
                "\n[bold yellow]⏹️ Speech stopped (Interrupted by user). Ready for next prompt.[/bold yellow]",
                "\n[Speech stopped. Ready for next prompt.]"
            )

        consumer.join(timeout=0.3)
        cleanup_session_files(session_id)
        _current_stop_event = None
        _current_item = None

        if item.on_end:
            try:
                item.on_end(interrupted=item.interrupted)
            except Exception:
                pass

        for cb in _global_on_end_callbacks:
            try:
                cb(interrupted=item.interrupted)
            except Exception:
                pass

        if item.done_event:
            item.done_event.set()


def _speech_queue_worker_loop():
    """Continuous daemon loop consuming speech items sequentially from the queue."""
    while True:
        try:
            item = _speech_queue.get()
            if item is None:
                break
            _play_speech_item(item)
            _speech_queue.task_done()
        except Exception as e:
            try:
                _speech_queue.task_done()
            except Exception:
                pass


# Launch persistent background queue worker
_worker_thread = threading.Thread(target=_speech_queue_worker_loop, daemon=True, name="SpeechQueueWorker")
_worker_thread.start()


# =========================================================================
# PUBLIC SPEAK API
# =========================================================================

def speak(text, allow_interrupt=True, priority=1, block=True, on_start=None, on_end=None):
    """
    Main speak function backed by a central sequential speech queue.
    - Multiple calls from different threads (e.g. user response, battery warning, email notification)
      will NEVER overlap. They are spoken strictly one-by-one in sequential priority order.
    - If allow_interrupt is True, users can press Ctrl+D, Esc, click mic, or submit a prompt to interrupt immediately.
    - If block is True, the calling thread waits until this speech item completes (ideal for synchronous CLI flows).
    - If block is False, the call returns immediately and plays in background sequence.
    """
    if not text or not str(text).strip():
        return True

    clean_text = str(text).strip()
    done_event = threading.Event() if block else None

    item = SpeechItem(
        text=clean_text,
        priority=priority,
        allow_interrupt=allow_interrupt,
        on_start=on_start,
        on_end=on_end,
        done_event=done_event
    )

    _speech_queue.put(item)

    if block:
        done_event.wait()
        return not item.interrupted
    return True
