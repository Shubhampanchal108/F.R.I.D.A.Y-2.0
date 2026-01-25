import os
import queue
import threading
import time
from playsound import playsound
from gtts import gTTS

audio_queue = queue.Queue()
STOP_SIGNAL = "STOP"


# Split text into chunks
def split_text(text):
    try:
        sentences = text.split(".")
        return [s.strip() for s in sentences if s.strip()]
    except Exception as e:
        print("❌ Split Error:", e)
        return []


# Producer: create audio files
def audio_producer(text):
    try:
        chunks = split_text(text)

        if not chunks:
            audio_queue.put(STOP_SIGNAL)
            return

        for index, chunk in enumerate(chunks):
            try:
                filename = f"Database//audio//voice_{index}.mp3"

                tts = gTTS(text=chunk)
                tts.save(filename)

                audio_queue.put(filename)

            except Exception as e:
                print(f"❌ TTS Error on chunk {index}:", e)

    except Exception as e:
        print("❌ Producer Crash:", e)

    finally:
        audio_queue.put(STOP_SIGNAL)


# Consumer: play audio files
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

                playsound(filename)
                time.sleep(0.1)

            except Exception as e:
                print("❌ Play Error:", e)

            finally:
                try:
                    if os.path.exists(filename):
                        os.remove(filename)
                except Exception as e:
                    print("❌ Delete Error:", e)

    except Exception as e:
        print("❌ Consumer Crash:", e)


# Main speak fucntion 
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