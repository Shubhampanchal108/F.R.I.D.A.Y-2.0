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


# ---------------- BRAIN (MULTI-TOOL AGENT LOOP) ---------------- #
def Brain(prompt: str, origin='server', source=None, tool_callback=None):
    if source is not None:
        origin = source
        
    # Dynamically fetch current configuration keys
    llm_key = Check_Keys("KEYS", "LLM_KEY")
    base_url = Check_Keys("LLM", "LLM_SERVICE_PROVIDER_URL")
    model = Check_Keys("LLM", "MODEL")

    client = OpenAI(
        base_url=base_url if base_url else None,
        api_key=llm_key,
    )

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
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0.3,
                messages=messages,
                timeout=25.0
            )

            if not response or not response.choices:
                return "Sir, the AI service returned an empty response. Please try asking again."

            msg = response.choices[0].message.content
            if not msg:
                return "Sir, I received an empty text reply from the language model."
            
            msg = msg.strip()

        except Exception as api_err:
            err_str = str(api_err)
            print(f"⚠️ LLM API Error: {err_str}")
            if "timeout" in err_str.lower():
                return "Sir, the LLM service connection timed out after 25 seconds. Please check your internet connection or try again."
            return f"Sir, I encountered an LLM API error: {err_str}. You can check your model/keys in /config."

        data = parse_tool_call(msg)

        # -------- TOOL MODE -------- #
        if data and tool_calls < MAX_TOOL_CALLS:
            tool_name = data.get("tool")
            args = data.get("args", {})

            if tool_name in TOOLS:
                tool_msg = f"Executing tool: {tool_name} {args if args else ''}"
                if tool_callback:
                    try:
                        tool_callback(tool_name, args)
                    except Exception:
                        pass
                else:
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
                    return f"Tool execution failed for '{tool_name}': {e}"

        # -------- FINAL HUMAN RESPONSE -------- #
        add_to_history("user", prompt)
        add_to_history("assistant", msg)

        return msg.replace("*", "")


# ---------------- RUN ---------------- #
if __name__ == "__main__":
    print("🤖 Friday Online — Vector Memory Activated\n")

    while True:
        inp = input("You: ")

        if inp.lower() in ["exit", "quit"]:
            print("Friday: Goodbye Sir. Have a productive day.")
            break

        reply = Brain(inp)
        print("Friday:", reply)
