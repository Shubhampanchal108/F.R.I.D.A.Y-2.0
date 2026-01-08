# speech_to_text_online.py
import speech_recognition as sr

def SpeechRecognition():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()  

    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        try:
            audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            pass

    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        pass
    except Exception as e:
        pass
