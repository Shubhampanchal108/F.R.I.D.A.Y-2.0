from Brain import Brain
from voice_input import SpeechRecognition
from speak import speak
from Tools.systems_tools import greet
from Tools.reminder import get_due_reminders
import os 
from dotenv import load_dotenv
import pygame

load_dotenv()
file_path = os.getenv("SOUND_FILE")

# ===== INIT PYGAME AUDIO =====
pygame.mixer.init()

if file_path and os.path.exists(file_path):
    try:
        pygame.mixer.music.load(file_path)
    except Exception as e:
        print("🔊 Sound Load Error:", e)

# ===== PROTOCOLS =====
VOCAL_SENSE_PROTOCOL = False
TYPE_ASSIST_PROTOCOL = True
AUDIO_DRIVE_PROTOCOL = True

VOICE_COMMANDS = ["switch to voice", "voice mode"]
TYPE_COMMANDS = ["switch to typing", "type mode"]

# ===== GREETING =====
greeting = greet()
print(greeting)
speak(f"{greeting} How may I assist you")

# ===== SAFE CLICK SOUND USING PYGAME =====
def play_click():
    if AUDIO_DRIVE_PROTOCOL and file_path and os.path.exists(file_path):
        try:
            pygame.mixer.music.play()
        except Exception as e:
            print("🔊 Play Error:", e)

# ===== PROCESS RESPONSE =====
def process_response(text):
    response = Brain(text)
    if response:
        final_ans = response.replace("*", "")
        print("Friday:", final_ans)
        if AUDIO_DRIVE_PROTOCOL:
            speak(final_ans)

# ===== MAIN LOOP =====
if __name__ == "__main__":

    while True:

        # ===== CHECK DUE REMINDERS =====
        try:
            due_reminders = get_due_reminders()
            for reminder in due_reminders:
                process_response(f"Reminder alert: '{reminder}' is due now!")
        except Exception as e:
            print("⏰ Reminder Error:", e)

        # ===== INPUT MODE =====
        if VOCAL_SENSE_PROTOCOL:
            print("🎙️ Listening...")
            try:
                query = SpeechRecognition()
            except Exception as e:
                print("🎤 Mic Error:", e)
                continue
        else:
            query = input("Enter chat: ")

        if not query:
            continue

        query_lower = query.lower().strip()
        print(f"Shubham : {query}\n")

        # ===== PROTOCOL SWITCH =====
        if any(cmd in query_lower for cmd in VOICE_COMMANDS):
            VOCAL_SENSE_PROTOCOL = True
            TYPE_ASSIST_PROTOCOL = False
            speak("Vocal sense protocol activated")
            print("🔁 Switched to VOICE mode")
            continue

        if any(cmd in query_lower for cmd in TYPE_COMMANDS):
            VOCAL_SENSE_PROTOCOL = False
            TYPE_ASSIST_PROTOCOL = True
            speak("Type assist protocol activated")
            print("🔁 Switched to TYPING mode")
            continue

        if "off" in query_lower and "audio drive" in query_lower:
            AUDIO_DRIVE_PROTOCOL = False
            speak("Disabling Audio drive protocol.")
            print("🔇 Audio drive disabled")
            continue

        if "activate" in query_lower and "audio drive" in query_lower:
            AUDIO_DRIVE_PROTOCOL = True
            speak("Activating Audio drive protocol.")
            print("🔊 Audio drive enabled")
            continue

        # ===== PLAY CLICK SOUND =====
        play_click()

        # ===== PROCESS USER QUERY =====
        clean_query = query_lower.replace("friday", "").strip()
        process_response(clean_query)

