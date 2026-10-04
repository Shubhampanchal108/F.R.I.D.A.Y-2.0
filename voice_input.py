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


def SpeechRecognition(input_language="en", timeout=6, phrase_time_limit=10):
    """
    Native, lightweight microphone speech recognition using Google Speech API.
    Does not launch external browsers or pollute the terminal with logs.
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        lang_code = "en-US" if input_language.lower() == "en" else input_language
        raw_text = recognizer.recognize_google(audio, language=lang_code).strip()

        if not raw_text:
            return None

        if input_language.lower() != "en":
            try:
                translated = UniversalTranslator(raw_text)
                return QueryModifier(translated)
            except Exception:
                return QueryModifier(raw_text)
        else:
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
