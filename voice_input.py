import os
import sys
import logging
import warnings
import mtranslate as mt
import speech_recognition as sr

# Suppress warnings and noisy third-party logs
warnings.filterwarnings("ignore")
logging.getLogger("speech_recognition").setLevel(logging.ERROR)


def QueryModifier(Query: str) -> str:
    """Format transcribed voice queries with proper capitalization and punctuation."""
    if not Query:
        return ""
    new_query = Query.lower().strip()
    question_words = [
        "how", "what", "when", "where", "who", "which",
        "why", "can you", "whom", "whose", "what's", "where's", "is", "are"
    ]
    if any(new_query.startswith(word) for word in question_words):
        if new_query[-1] not in [".", "?", "!"]:
            new_query += "?"
    else:
        if new_query[-1] not in [".", "?", "!"]:
            new_query += "."
    return new_query.capitalize()


def UniversalTranslator(Text: str) -> str:
    """Translate non-English voice input to English if needed."""
    try:
        english_translation = mt.translate(Text, "en", "auto")
        return english_translation.capitalize()
    except Exception:
        return Text


def SpeechRecognition(input_language="en", timeout=8, phrase_time_limit=20):
    """
    Robust microphone speech recognition using Google Speech API.
    Configured with a generous 1.8s pause threshold so it never cuts off speech mid-sentence.
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 350
    recognizer.dynamic_energy_threshold = False  # Fixed threshold to prevent fading out sentence tails
    recognizer.pause_threshold = 1.8             # Allows natural breathing & pauses without cutting off
    recognizer.non_speaking_duration = 1.2

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        # en-IN recognizes Indian English & Hinglish significantly better than en-US
        lang_code = "en-IN" if input_language.lower() in ["en", "en-us"] else input_language
        raw_text = recognizer.recognize_google(audio, language=lang_code).strip()

        if not raw_text:
            return None

        return QueryModifier(raw_text)

    except (sr.WaitTimeoutError, sr.UnknownValueError):
        return None
    except Exception:
        return None


if __name__ == "__main__":
    print("🎙️ Testing SpeechRecognition (Speak into microphone)...")
    res = SpeechRecognition("en", timeout=5, phrase_time_limit=5)
    if res:
        print("Heard:", res)
    else:
        print("No speech detected.")
