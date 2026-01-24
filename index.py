from Brain import Brain
from voice_input import SpeechRecognition
from speak import speak
from playsound import playsound
from Tools.systems_tools import greet
from Tools.reminder import get_due_reminders
import os 
from dotenv import load_dotenv

load_dotenv()
file_path = os.getenv("SOUND_FILE")

# ===== PROTOCOLS =====
VOCAL_SENSE_PROTOCOL = False
TYPE_ASSIST_PROTOCOL = True
AUDIO_DRIVE_PROTOCOL = False

if __name__ == "__main__":

    print(greet())
    speak(f"{greet()} How may I assist You")

    while True:

        # ===== CHECK DUE REMINDERS =====
        due_reminders = get_due_reminders()
        for reminder in due_reminders:
            # Pass to Brain for smart alert
            response = Brain(f"Reminder alert: '{reminder}' is due now!")
            if response:
                final_ans = response.replace("*", "")
                print("Friday:", final_ans)
                speak(final_ans)

        # ===== INPUT MODE =====
        if VOCAL_SENSE_PROTOCOL:
            print("🎙️ Listening...")
            query = SpeechRecognition()
        else:
            query = input("Enter chat: ")

        if not query:
            continue

        query_lower = query.lower()

        # ===== PROTOCOL SWITCH =====
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

        if "off" in query_lower and "audio drive"  in query_lower:
            speak("Disabling Audio drive protocol.")
            AUDIO_DRIVE_PROTOCOL = False
            continue

        if "activate" in query_lower and "audio drive"  in query_lower:
            speak("Activating Audio drive protocol.")
            AUDIO_DRIVE_PROTOCOL = True
            continue

        # ===== PLAY CLICK SOUND =====
        playsound(file_path)
        print(f"Shubham : {query}\n")

        # ===== PROCESS USER QUERY THROUGH BRAIN =====
        response = Brain(query_lower.replace("friday", ""))

        if response:
            final_ans = response.replace("*", "")
            print("Friday:", final_ans)
            
            if (AUDIO_DRIVE_PROTOCOL):
                speak(final_ans)
