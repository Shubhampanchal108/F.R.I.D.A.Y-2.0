import speech_recognition as sr

def SpeechRecognition():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=8)
            except sr.WaitTimeoutError:
                return None

        if audio:
            text = recognizer.recognize_google(audio)
            return text.strip() if text else None
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"\n⚠️ Google Speech Recognition API Error: {e}\n")
        return None
    except Exception:
        return None
