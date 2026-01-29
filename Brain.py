from openai import OpenAI  # type: ignore
from utiles import load_memory, add_to_history, normalize_role, parse_tool_call
import os
import sys
from dotenv import load_dotenv

# Allow parent directory imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

#Tools Imorts
from Tools.weather import get_current_weather
from Tools.systems_tools import *
from Tools.News import get_latest_news
from Tools.wikipedia import search_wikipedia
from Tools.pywhatkit import *
from Tools.Emails import send_email, read_latest_emails, readmail_Full_body
from Tools.Date_Time import get_date_with_day, get_current_time
from Tools.Media_Tools import *
from Tools.Todo import add_task, list_tasks, delete_task, complete_task
from Tools.reminder import *
from Tools.website_opner import open_website
from Tools.File_manger import *
from Tools.Mobile_Automation import check_connection_json, connect_mobile_with_bat, unlock_device, send_whatsapp_message, phone_call_with_mobile
from RAG import save_longterm_memory, search_vector_memory
from configs import Friday_Instruction


# ---------------- ENV ---------------- #
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_API_KEY,
)

# ---------------- TOOLS ---------------- #
TOOLS = {
    "get_weather": get_current_weather,
    "get_News": get_latest_news,
    "check_battery": get_battery_status,
    "search_wikipedia": search_wikipedia,
    "google_search": google_search,
    "open_app": open_application,
    "check_cpu": get_cpu_status,
    "clear_recycle_bin": empty_recycle_bin,
    "youtube_automation": play_youtube,
    "close_app": close_app,
    "find_my_ip": find_my_ip,
    "send_email": send_email,
    "read_latest_emails": read_latest_emails,
    "get_current_time": get_current_time,
    "get_date_with_day": get_date_with_day,
    "brightness_down": brightness_down,
    "brightness_up": brightness_up,
    "volume_down": volume_down,
    "volume_up": volume_up,
    "mute_volume": mute_volume,
    "unmute_volume": unmute_volume,
    "yt_play_pause": yt_play_pause,
    "yt_next": yt_next,
    "yt_previous": yt_previous,
    "yt_fullscreen": yt_fullscreen,
    "capture_screenshot": capture_screenshot,
    "add_task": add_task,
    "list_tasks": list_tasks,
    "delete_task": delete_task,
    "complete_task": complete_task,
    "add_reminder": add_reminder,
    "list_reminders": list_reminders,
    "delete_reminder_by_name": delete_reminder_by_name,
    "get_due_reminders": get_due_reminders,
    "open_website": open_website,
    "readmail_Full_body": readmail_Full_body,
    'create_and_open_file': create_and_open_file,
    'read_file': read_file,
    'update_file': update_file,
    'delete_file': delete_file,
    'list_files': list_files,
    'rename_file': rename_file,
    'search_file_in_folder': search_file_in_folder,
    'connect_mobile_with_bat': connect_mobile_with_bat,
    'check_connection_json': check_connection_json,
    'unlock_device': unlock_device,
    'send_whatsapp_message': send_whatsapp_message,
    'phone_call_with_mobile': phone_call_with_mobile,
    'minimize_active_window': minimize_active_window,
    'save_longterm_memory': save_longterm_memory,
}

# ---------------- BRAIN (MULTI-TOOL AGENT LOOP) ---------------- #
def Brain(prompt: str):
    memory = load_memory()
    history = memory.get("conversation_history", [])

    messages = [{"role": "system", "content": Friday_Instruction}]

    # 🧠 Load previous chat history
    for m in history:
        messages.append({
            "role": normalize_role(m.get("role", "user")),
            "content": m.get("content", "")
        })

    # Retrieve relevant vector memories and include them in the context
    try:
        retrieved = search_vector_memory(query=prompt, top_k=3)
        if retrieved:
            mem_texts = []
            for mem in retrieved:
                txt = mem.get("text", "").replace("\n", " ")
                md = mem.get("metadata", {}) or {}
                tags = md.get("tags", "")
                mem_texts.append(f"- {txt} (tags: {tags})")

            memories_str = "\n".join(mem_texts)
            messages.append({
                "role": "assistant",
                "content": f"Relevant memories:\n{memories_str}"
            })
    except Exception as e:
        print("⚠️ Memory retrieval error:", e)

    # User prompt
    messages.append({"role": "user", "content": prompt})

    MAX_TOOL_CALLS = 5
    tool_calls = 0

    while True:
        response = client.chat.completions.create(
            model="Qwen/Qwen3-Coder-480B-A35B-Instruct:novita",
            temperature=0.2,
            messages=messages
        )

        msg = response.choices[0].message.content.strip()

        data = parse_tool_call(msg)

        # -------- TOOL MODE -------- #
        if data and tool_calls < MAX_TOOL_CALLS:
            tool_name = data.get("tool")
            args = data.get("args", {})

            if tool_name in TOOLS:
                print(f"🔧 Tool called → {tool_name} {args}")

                try:
                    tool_result = TOOLS[tool_name](**args)
                    messages.append({
                        "role": "assistant",
                        "content": msg
                    })

                    messages.append({
                        "role": "assistant",
                        "content": f"Tool output: {tool_result}"
                    })

                    tool_calls += 1
                    continue

                except Exception as e:
                    print("⚠️ Tool Error:", e)
                    add_to_history("assistant", f"Tool error: {e}")
                    return "Tool execution failed. Please try again."

        # -------- FINAL HUMAN RESPONSE -------- #
        add_to_history("user", prompt)
        add_to_history("assistant", msg)

        return msg.replace("*", "")


# ---------------- RUN ---------------- #
if __name__ == "__main__":
    print("🤖 Friday v2.0 Online — Vector Memory Activated\n")

    while True:
        inp = input("You: ")

        if inp.lower() in ["exit", "quit"]:
            print("Friday: Goodbye Sir. Have a productive day.")
            break

        reply = Brain(inp)
        print("Friday:", reply)
