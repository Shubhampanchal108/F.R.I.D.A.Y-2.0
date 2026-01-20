import json 
import os
import re
from dotenv import load_dotenv

load_dotenv()

MEMORY_FILE = os.getenv("MEMORY_FILE")
MAX_HISTORY = 15

# ---------------- MEMORY ---------------- #
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"conversation_history": []}

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)


def add_to_history(role, content):
    memory = load_memory()
    memory.setdefault("conversation_history", [])

    memory["conversation_history"].append({
        "role": role,
        "content": content
    })

    memory["conversation_history"] = memory["conversation_history"][-MAX_HISTORY:]
    save_memory(memory)


# ---------------- UTILITIES ---------------- #
def clean_json_string(msg: str) -> str:
    msg = msg.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    msg = msg.replace("\n", "").replace("\r", "")
    msg = re.sub(r",\s*}", "}", msg)
    msg = re.sub(r",\s*]", "]", msg)
    return msg.strip()