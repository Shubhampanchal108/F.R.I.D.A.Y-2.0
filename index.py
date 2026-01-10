from Brain import Brain
from voice_input import SpeechRecognition
from speak import speak
from playsound import playsound
from Tools.systems_tools import greet

file_path = r"C:\Users\j\OneDrive\Desktop\shubham studio\F.R.I.D.A.Y\Database\docs\mixkit-sci-fi-click-900.wav"

if __name__ == "__main__":

    print(greet())
    speak(greet())

    # Protocols
    VOCAL_SENSE_PROTOCOL = False
    TYPE_ASSIST_PROTOCOL = True

    while True:

        # ===== INPUT MODE =====
        if VOCAL_SENSE_PROTOCOL:
            print("🎙️ Listening...")
            query = SpeechRecognition()   # your function
        else:
            query = input("⌨️ Enter chat: ")

        if not query:
            continue

        query_lower = query.lower()

        # ===== PROTOCOL SWITCH COMMANDS =====
        if "switch to voice" in query_lower or "voice mode" in query_lower:
            VOCAL_SENSE_PROTOCOL = True
            TYPE_ASSIST_PROTOCOL = False
            speak("Vocal sense protocol activated")
            print("🔁 Switched to VOICE mode")
            continue

        if "switch to typing" in query_lower or "type mode" in query_lower:
            VOCAL_SENSE_PROTOCOL = False
            TYPE_ASSIST_PROTOCOL = True
            speak("Type assist protocol activated")
            print("🔁 Switched to TYPING mode")
            continue

        playsound(file_path)
        print(f"User: {query}\n")

        response = Brain(query_lower.replace("friday", ""))

        if response:
            final_ans = response.replace("*", "")
            print("Friday:", final_ans)
            speak(final_ans)
         
