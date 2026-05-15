import os
import queue
import threading
import time
from gtts import gTTS
from path import AUDIO_PATH

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

# ===============================
# INIT PYGAME AUDIO
# ===============================
pygame.mixer.init()

audio_queue = queue.Queue()
STOP_SIGNAL = "STOP"

AUDIO_FOLDER = AUDIO_PATH
os.makedirs(AUDIO_FOLDER, exist_ok=True)

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
def audio_producer(text):
    try:
        chunks = split_text(text)

        if not chunks:
            audio_queue.put(STOP_SIGNAL)
            return

        for index, chunk in enumerate(chunks):
            try:
                filename = f"{AUDIO_FOLDER}/voice_{index}.mp3"

                tts = gTTS(text=chunk)
                tts.save(filename)

                audio_queue.put(filename)

            except Exception as e:
                print(f"❌ TTS Error on chunk {index}:", e)

    except Exception as e:
        print("❌ Producer Crash:", e)

    finally:
        audio_queue.put(STOP_SIGNAL)


# ===============================
# Consumer: play audio using pygame
# ===============================
def audio_consumer():
    try:
        while True:
            filename = audio_queue.get()

            if filename == STOP_SIGNAL:
                break

            try:
                if not os.path.exists(filename):
                    print("⚠️ File not found:", filename)
                    continue

                # ▶️ Load & play
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()

                # ⏳ Wait until playback finishes
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)

                # 🛑 Release file lock properly (WINDOWS FIX)
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                time.sleep(0.1)

            except Exception as e:
                print("❌ Play Error:", e)

            finally:
                # 🧹 Safe delete with retry
                for _ in range(5):
                    try:
                        if os.path.exists(filename):
                            os.remove(filename)
                            break
                    except Exception:
                        time.sleep(0.1)

    except Exception as e:
        print("❌ Consumer Crash:", e)


# ===============================
# Main speak function
# ===============================
def speak(text):
    try:
        if not text.strip():
            print("⚠️ Empty text received")
            return

        producer = threading.Thread(target=audio_producer, args=(text,))
        consumer = threading.Thread(target=audio_consumer)

        producer.start()
        consumer.start()

        producer.join()
        consumer.join()

    except Exception as e:
        print("❌ Speak Function Error:", e)
