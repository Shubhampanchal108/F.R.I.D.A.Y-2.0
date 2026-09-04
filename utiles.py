import json 
import os
import re
from path import CHATS_PATH, DOCS_PATH


MEMORY_FILE = os.path.join(CHATS_PATH, "memory.json")
CONFIG_FILE = os.path.join(DOCS_PATH, "config.json")
MAX_HISTORY = 30

# ---------------- MEMORY ---------------- #
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)

        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"conversation_history": []}, f)

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

    # Compact history when it exceeds the limit (summarize old messages)
    if len(memory["conversation_history"]) > MAX_HISTORY:
        memory["conversation_history"] = _compact_history(memory["conversation_history"])

    save_memory(memory)


def _compact_history(history):
    """Summarize oldest messages and keep recent ones, preserving context."""
    if len(history) <= MAX_HISTORY:
        return history

    old_messages = history[:-20]
    recent_messages = history[-20:]

    # Build a simple summary of old messages as fallback
    summary_parts = []
    for msg in old_messages[-10:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")[:100]
        summary_parts.append(f"{role}: {content}")

    summary_text = "Earlier conversation summary: " + " | ".join(summary_parts)

    # Try LLM-powered summarization for better quality
    try:
        from openai import OpenAI
        from config_driver import Check_Keys

        llm_key = Check_Keys("KEYS", "LLM_KEY")
        base_url = Check_Keys("LLM", "LLM_SERVICE_PROVIDER_URL")
        model_name = Check_Keys("LLM", "MODEL")

        client = OpenAI(
            base_url=base_url if base_url else None,
            api_key=llm_key,
        )

        conv_text = "\n".join(
            [f"{m.get('role','user')}: {m.get('content','')[:150]}" for m in old_messages[-15:]]
        )

        response = client.chat.completions.create(
            model=model_name,
            messages=[{
                "role": "user",
                "content": f"Summarize this conversation in 2-3 sentences. Focus on key topics and decisions:\n{conv_text}"
            }],
            temperature=0.2,
            timeout=8.0
        )
        summary_text = "Earlier conversation summary: " + response.choices[0].message.content.strip()
    except Exception:
        pass  # Use the simple fallback summary

    return [{"role": "system", "content": summary_text}] + recent_messages


# ---------------- UTILITIES ---------------- #
def clean_json_string(msg: str) -> str:
    msg = msg.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    msg = msg.replace("\n", "").replace("\r", "")
    msg = re.sub(r",\s*}", "}", msg)
    msg = re.sub(r",\s*]", "]", msg)
    return msg.strip()

# ---------------- HELPERS ---------------- #
def normalize_role(role: str):
    if role in ["system", "user", "assistant"]:
        return role
    if role in ["human"]:
        return "user"
    if role in ["ai", "bot", "model"]:
        return "assistant"
    return "user"


def parse_tool_call(msg: str):
    try:
        match = re.search(r'\{[\s\S]*\}', msg)
        if not match:
            return None

        json_str = clean_json_string(match.group())
        data = json.loads(json_str)

        if isinstance(data, dict) and "tool" in data:
            return data
        return None
    except Exception:
        return None

# ---------------- CONFIGS ---------------- #

Default_Data = {
  "KEYS": 
    {
      "WEATHER_KEY": "",
      "LLM_KEY": "",
      "EMAIL": "",
      "PASSWORD": "",
      "AGENT_PASSWORD": "",
      "TAVILY_API_KEY":"",
      "NEWS_API_KEY": "",
      "MONGODB_URL": "mongodb://localhost:27017/"
    },

  "LLM" :
    {
      "LLM_SERVICE_PROVIDER_URL": "",
      "MODEL": ""
    },

  "USER":
    {
      "Name": "",
      "email": "",
      "phone_number": "",
      "github": "",
      "linkedin": ""
    }
}


def search(key):
    try:
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w") as file:
                json.dump(Default_Data, file, indent=4)

        # ✅ read file
        with open(CONFIG_FILE, "r") as file:
            data = json.load(file)

        # ✅ search key
        return data.get(key, "Key not found ❌")

    except json.JSONDecodeError:
        return "Invalid JSON ❌"

search("KEYS")