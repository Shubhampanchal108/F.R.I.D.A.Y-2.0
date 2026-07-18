from openai import OpenAI  # type: ignore
from utiles import load_memory, add_to_history, normalize_role, parse_tool_call
import os
import sys

# Allow parent directory imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RAG import search_vector_memory
from configs import Friday_Instruction
from Tool_guard import load_tools, execute_tool, TOOLS
from config_driver import Check_Keys

registry = load_tools()

# ---------------- ENV ---------------- #
LLM_KEY = Check_Keys("KEYS", "LLM_KEY")
BASE_URL = Check_Keys("LLM", "LLM_SERVICE_PROVIDER_URL")
MODEL = Check_Keys("LLM", "MODEL")

client = OpenAI(
    base_url=BASE_URL,
    api_key=LLM_KEY,
)


# ---------------- BRAIN (MULTI-TOOL AGENT LOOP) ---------------- #
def Brain(prompt: str, origin='server'):
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

    MAX_TOOL_CALLS = 4
    tool_calls = 0

    while True:
        response = client.chat.completions.create(
            model= MODEL,
            temperature=0.3,
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
                    tool_result = execute_tool(
                        tool_name=tool_name,
                        origin=origin,
                        **args
                    )
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
