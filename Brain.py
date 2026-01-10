from openai import OpenAI  # type: ignore
from utiles import load_memory, add_to_history, clean_json_string
import os
import sys
import json
from dotenv import load_dotenv
# Allow parent directory imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Tools.weather import get_current_weather
from Tools.systems_tools import *
from Tools.News import get_latest_news
from Tools.wikipedia import search_wikipedia
from Tools.pywhatkit import *
from Tools.content_generator import write_to_notepad
from Tools.Emails import send_email, read_latest_emails
from Tools.Date_Time import get_date_with_day, get_current_time
from Tools.Media_Tools import *
from configs import Friday_Instruction

load_dotenv()

# ---------------- CONFIG ---------------- #
HF_API_KEY = os.getenv("HF_API_KEY")

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_API_KEY,
)


TOOLS = {
    "get_weather": get_current_weather,
    "get_News": get_latest_news,
    "check_battery": get_battery_status,
    "search_wikipedia": search_wikipedia,
    "google_search": google_search,
    "generate_content": write_to_notepad,
    "open_app": open_application,
    "check_cpu": get_cpu_status,
    "clear_recycle_bin": empty_recycle_bin,
    "youtube_automation": play_youtube,
    "close_app": close_app,
    "find_my_ip": find_my_ip,
    "send_email": send_email,
    "read_latest_emails": read_latest_emails,
    'get_current_time': get_current_time,
    'get_date_with_day': get_date_with_day,
    'brightness_down':brightness_down,
    'brightness_up': brightness_up,
    'volume_down': volume_down,
    'volume_up': volume_up,
    'mute_volume': mute_volume,
    "unmute_volume": unmute_volume,
    'yt_play_pause': yt_play_pause,
    'yt_next': yt_next,
    "yt_previous" : yt_previous,
    'yt_fullscreen': yt_fullscreen,
    'capture_screenshot': capture_screenshot,
    
}


def parse_tool_call(msg: str):
    try:
        data = json.loads(clean_json_string(msg))
        return data
    except json.JSONDecodeError:
        return None


# ---------------- BRAIN ---------------- #
def Brain(prompt: str):
    memory = load_memory()
    history = memory.get("conversation_history", [])

    messages = [{"role": "system", "content": Friday_Instruction}]

    for m in history:
        messages.append(m)

    messages.append({"role": "user", "content": prompt})

    # -------- First LLM Call -------- #
    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-72B-Instruct",
        temperature=0.3,
        messages=messages
    )

    msg = response.choices[0].message.content.strip()

    # -------- Tool Detection -------- #
    data = parse_tool_call(msg)
    if data:
        tool_name = data.get("tool")
        args = data.get("args", {})

        if tool_name in TOOLS:
            print(f"🔧 Tool called → {tool_name} {args}")
            try:
                tool_result = TOOLS[tool_name](**args)
                print("🤖 Tool output:", tool_result)

                messages.append({
                    "role": "assistant",
                    "content": f"Tool output: {tool_result}"
                })

                # -------- Final LLM Reply -------- #
                final_response = client.chat.completions.create(
                    model="Qwen/Qwen2.5-72B-Instruct",
                    temperature=0.5,
                    messages=messages
                )

                human_text = final_response.choices[0].message.content.strip()

                add_to_history("user", prompt)
                add_to_history("assistant", human_text)

                return human_text

            except Exception as e:
                print("⚠️ Tool Error:", e)
                return "Sorry sir, tool execution failed."

    # -------- Normal Reply -------- #
    add_to_history("user", prompt)
    add_to_history("assistant", msg)

    return msg

if __name__ == "__main__":
    while True:
        inp  = input("Enter a chat: ")
        print(Brain(inp))