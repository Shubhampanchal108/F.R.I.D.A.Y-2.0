# ✅ Required Imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from subprocess import DEVNULL
import os
import mtranslate as mt
import logging
import time
import random

# ✅ Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ✅ Custom Path Setup
custom_path = r"C:\Users\j\OneDrive\Desktop\shubham studio\JARVIS AI\Data"
html_file_path = os.path.join(custom_path, "Voice.html")

# ✅ HTML Code for JS Speech Recognition
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head><title>Speech Recognition</title></head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'en';
        recognition.continuous = true;

        function startRecognition() {
            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript + ' ';
            };
            recognition.onend = function() { recognition.start(); };
            recognition.start();
        }
        function stopRecognition() { recognition.stop(); }
    </script>
</body>
</html>'''

# ✅ Write HTML File
os.makedirs(custom_path, exist_ok=True)
with open(html_file_path, "w") as f:
    f.write(HtmlCode)

# ✅ Chrome Driver Setup
Link = f"file:///{html_file_path.replace(os.sep, '/')}"
chrome_options = Options()
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--disable-logging")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless=new")  # Optional: remove to see browser

service = Service(ChromeDriverManager().install(), log_path=os.devnull)
driver = webdriver.Chrome(service=service, options=chrome_options)

# ✅ Query Formatter
def QueryModifier(Query):
    new_query = Query.lower().strip()
    question_words = ["how", "what", "when", "where", "who", "which", "why", "can you", "whom", "whose", "what's", "where's"]
    if any(new_query.startswith(word) for word in question_words):
        if new_query[-1] not in [".", "?", "!"]:
            new_query += "?"
    else:
        if new_query[-1] not in [".", "?", "!"]:
            new_query += "."
    return new_query.capitalize()

# ✅ Translate to English if needed
def UniversalTranslator(Text):
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation.capitalize()

# ✅ Idle-Aware Voice Recognition
def SpeechRecognition(input_language="en", idle_timeout=10):
    driver.get(Link)
    
    while True: 
        driver.find_element(By.ID, "start").click()
        start_time = time.time()
        last_text = ""

        while True:  
            try:
                text = driver.find_element(By.ID, "output").text.strip()

                # Press Enter to skip and restart listening
                import msvcrt
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\r':
                        driver.find_element(By.ID, "end").click()
                        print("Enter pressed. Restarting listening...")
                        break

                if text and text != last_text:
                    last_text = text

                if text:
                    driver.find_element(By.ID, "end").click()
                    return QueryModifier(text) if input_language.lower() == "en" else QueryModifier(UniversalTranslator(text))

                if time.time() - start_time > idle_timeout:
                    driver.find_element(By.ID, "end").click()
                    return None

            except Exception as e:
                logging.error("SpeechRecognition error: %s", e)
                driver.find_element(By.ID, "end").click()
                return None

if __name__ == "__main__":
    while True:
        result = SpeechRecognition("en", idle_timeout=30)
        if result:
            print("🎙️ You said:", result)
        else:
            print("🕒 No speech detected (idle)")



# import speech_recognition as sr

# def SpeechRecognition():
#     recognizer = sr.Recognizer()
#     mic = sr.Microphone()

#     try:
#         with mic as source:
#             recognizer.adjust_for_ambient_noise(source, duration=0.5)
#             try:
#                 audio = recognizer.listen(source, timeout=3, phrase_time_limit=8)
#             except sr.WaitTimeoutError:
#                 return None

#         if audio:
#             text = recognizer.recognize_google(audio)
#             return text.strip() if text else None
#     except sr.UnknownValueError:
#         return None
#     except sr.RequestError as e:
#         print(f"\n⚠️ Google Speech Recognition API Error: {e}\n")
#         return None
#     except Exception:
#         return None
