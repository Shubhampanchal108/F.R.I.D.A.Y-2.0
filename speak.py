import os
from playsound import playsound
from gtts import gTTS


# Friday Voice
def speak(text, output_file=r"C:\Users\j\OneDrive\Desktop\shubham studio\JARVIS AI\Data\voice.mp3"):
    try:
        tts = gTTS(text=text)
        tts.save(output_file)
        playsound(output_file)

    finally:
        if os.path.exists(output_file):
            os.remove(output_file)


