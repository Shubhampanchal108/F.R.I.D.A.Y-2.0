from Brain import Brain
from voice_input import SpeechRecognition
from speak import speak
from Tools.systems_tools import greet
from config_driver import Check_Keys

AUTH_PASSWORD = Check_Keys("KEYS", "AGENT_PASSWORD")

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
        password = input("Enter password: ")

        if (password == AUTH_PASSWORD):
            print("✅ Authentication successful. Welcome back, Sir!\n")
            break
        else:
            print("Wrong password sir. Do you remember what you enter in the AGETN_PASSWORD when you are configring the agent.\n")

    while True:
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

        # ===== PROCESS USER QUERY =====
        clean_query = query_lower.replace("friday", "").strip()
        process_response(clean_query)

