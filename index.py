from Brain import Brain
from voice_input import SpeechRecognition
from speak import speak
from playsound import playsound

file_path = r"C:\Users\j\OneDrive\Desktop\shubham studio\F.R.I.D.A.Y\Database\docs\mixkit-sci-fi-click-900.wav"

if __name__ == "__main__":

    VOICE_ASSIST_PROTOCOL = True

    while VOICE_ASSIST_PROTOCOL:
        query = SpeechRecognition()

        # Safety check: speech may return None or empty string
        if not query:
            continue

        query_lower = query.lower()
        # Wake word check
        if query_lower:
            playsound(file_path)
            print(f"User: {query}\n")
            response = Brain(query_lower.replace("friday", ""))

            if response:
                final_ans = response.replace("*", "")
                print(final_ans)
                speak(final_ans)

            
