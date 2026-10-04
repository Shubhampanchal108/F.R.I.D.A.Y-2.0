from openai import OpenAI  # type: ignore
from utiles import load_memory, add_to_history, normalize_role, parse_tool_call
import json
import os
import sys

# Allow parent directory imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RAG import search_vector_memory
from memory_controller import auto_extract_memories, get_last_session_context, get_user_profile_summary
from configs import Friday_Instruction
from Tool_guard import load_tools, execute_tool, TOOLS
from config_driver import Check_Keys

registry = load_tools()

ACTION_TOOLS = {
    # Files
    "create_and_open_file", "read_file", "open_file", "update_file", "delete_file", "rename_file",
    # Apps & Windows
    "open_app", "close_app", "clear_recycle_bin",
    "minimize_active_window", "maximize_active_window",
    # Audio & Display
    "volume_up", "volume_down", "mute_volume", "unmute_volume",
    "brightness_up", "brightness_down", "capture_screenshot",
    # Media
    "youtube_automation", "yt_play_pause", "yt_next", "yt_previous", "yt_fullscreen",
    # Tasks & Reminders
    "add_task", "delete_task", "complete_task",
    "add_reminder", "delete_reminder_by_name",
    # Mobile
    "connect_mobile_with_bat", "unlock_device", "send_whatsapp_message", "phone_call_with_mobile"
}


def format_fallback_response(tool_name: str, args: dict, result) -> str:
    """Fallback generator to guarantee natural language response if LLM returns JSON or fails."""
    if not tool_name:
        return "Sir, I have completed the request."

    if isinstance(result, dict) and "error" in result:
        return f"Sir, I encountered an issue: {result.get('error')}."

    if tool_name == "get_weather":
        if isinstance(result, dict):
            city = result.get("city") or args.get("city", "your area")
            weather = result.get("weather", "clear")
            temp = result.get("temperature_c", "N/A")
            feels = result.get("feels_like_c", "N/A")
            return f"Sir, the weather in {city} is currently {weather} with a temperature of {temp}°C (feels like {feels}°C)."
        return f"Sir, here is the weather information: {result}."

    if tool_name == "check_battery":
        if isinstance(result, dict):
            pct = result.get("battery_percentage", "N/A")
            status = result.get("status", "Not charging")
            return f"Sir, your battery is at {pct}% ({status})."

    if tool_name == "check_cpu":
        if isinstance(result, dict):
            return f"Sir, the current CPU usage is {result.get('cpu_usage_percent', 'N/A')}%."

    if tool_name in ["get_current_time", "get_date_with_day"]:
        if isinstance(result, dict):
            return f"Sir, today is {result.get('day', '')}, {result.get('date', '')}."
        return f"Sir, the current time is {result}."

    if tool_name == "find_my_ip":
        if isinstance(result, dict):
            return f"Sir, your device IP address is {result.get('ip', 'unknown')}."

    if tool_name == "open_app":
        app = args.get("app") or args.get("application", "the application")
        return f"Sir, I have opened {app}."

    if tool_name == "close_app":
        app = args.get("app") or args.get("application", "the application")
        return f"Sir, I have closed {app}."

    if tool_name == "volume_up":
        return "Sir, the volume has been increased."

    if tool_name == "volume_down":
        return "Sir, the volume has been decreased."

    if tool_name == "mute_volume":
        return "Sir, audio has been muted."

    if tool_name == "unmute_volume":
        return "Sir, audio has been unmuted."

    if tool_name == "clear_recycle_bin":
        return "Sir, the recycle bin has been cleared."

    if tool_name == "capture_screenshot":
        return "Sir, screenshot has been captured."

    if tool_name == "add_task":
        task = args.get("task_text", "your task")
        return f"Sir, task '{task}' has been added to your to-do list."

    if tool_name == "list_tasks":
        if isinstance(result, list):
            tasks_str = ", ".join([str(t) for t in result]) if result else "none"
            return f"Sir, here are your tasks: {tasks_str}."

    if tool_name == "add_reminder":
        rem = args.get("reminder_text", "your reminder")
        t = args.get("remind_at", "")
        return f"Sir, reminder for '{rem}' at {t} has been set."

    if isinstance(result, dict) and "message" in result:
        return f"Sir, {result['message']}."

    if isinstance(result, str) and len(result) < 150 and not result.strip().startswith("{"):
        return f"Sir, {result}"

    return "Sir, the task has been completed successfully."


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

    # Cross-session continuity — inject last session context
    try:
        last_session = get_last_session_context()
        if last_session:
            messages.append({
                "role": "system",
                "content": f"[LAST SESSION CONTEXT] {last_session}"
            })
    except Exception:
        pass

    # Dynamic user profile — inject learned preferences & facts
    try:
        profile_summary = get_user_profile_summary()
        if profile_summary:
            messages.append({
                "role": "system",
                "content": f"[USER PROFILE]\n{profile_summary}"
            })
    except Exception:
        pass

    # Retrieve relevant vector memories with relevance filtering
    try:
        retrieved = search_vector_memory(query=prompt, top_k=5)
        if retrieved:
            mem_texts = []
            for mem in retrieved:
                txt = mem.get("text", "").replace("\n", " ")
                md = mem.get("metadata", {}) or {}
                tags = md.get("tags", "")
                importance = md.get("importance", "medium")
                mem_texts.append(f"- {txt} (tags: {tags}, importance: {importance})")

            memories_str = "\n".join(mem_texts)
            messages.append({
                "role": "system",
                "content": f"[MEMORY CONTEXT] Relevant memories about the user:\n{memories_str}"
            })
    except Exception:
        pass

    # User prompt
    messages.append({"role": "user", "content": prompt})

    MAX_TOOL_CALLS = 4
    tool_calls = 0
    executed_calls = set()
    last_tool_name = None
    last_tool_args = {}
    last_tool_result = None

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
            if "timeout" in err_str.lower():
                return "Sir, the LLM service connection timed out after 25 seconds. Please check your internet connection or try again."
            return f"Sir, I encountered an LLM API error: {err_str}. You can check your model/keys in /config."

        data = parse_tool_call(msg)

        # -------- TOOL MODE -------- #
        if data and tool_calls < MAX_TOOL_CALLS:
            tool_name = data.get("tool")
            args = data.get("args", {}) or {}

            # Create signature to detect duplicate calls
            call_sig = (tool_name, json.dumps(args, sort_keys=True))

            if call_sig in executed_calls:
                # LLM repeated the same tool call with same arguments! Block it.
                messages.append({
                    "role": "assistant",
                    "content": msg
                })
                messages.append({
                    "role": "user",
                    "content": (
                        f"[SYSTEM DIRECTIVE]: You have ALREADY executed '{tool_name}' with these exact arguments. "
                        f"Previous result was: {last_tool_result}\n"
                        f"Do NOT call '{tool_name}' again. "
                        f"Now respond directly to Sir in polite, natural language (English/Hindi as appropriate) "
                        f"explaining or confirming the results."
                    )
                })
                tool_calls += 1
                continue

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
                    tool_calls += 1
                    executed_calls.add(call_sig)
                    last_tool_name = tool_name
                    last_tool_args = args
                    last_tool_result = tool_result

                    # For pure action tools that succeeded, we can immediately return a clean response
                    is_action = tool_name in ACTION_TOOLS
                    is_success = not (isinstance(tool_result, dict) and "error" in tool_result)

                    if is_action and is_success:
                        action_reply = format_fallback_response(tool_name, args, tool_result)
                        add_to_history("user", prompt)
                        add_to_history("assistant", action_reply)
                        return action_reply

                    # For info/data tools: append to messages with USER role so model can synthesize
                    messages.append({
                        "role": "assistant",
                        "content": msg
                    })

                    res_str = str(tool_result)
                    if len(res_str) > 1200:
                        res_str = res_str[:1200] + "... [truncated]"

                    messages.append({
                        "role": "user",
                        "content": (
                            f"[TOOL OUTPUT FOR '{tool_name}']:\n{res_str}\n\n"
                            f"[SYSTEM INSTRUCTION]: The tool '{tool_name}' has executed successfully. "
                            f"Do NOT call '{tool_name}' again. Do NOT output JSON. "
                            f"Now speak directly to Sir in polite, natural language explaining the results."
                        )
                    })
                    continue

                except Exception as e:
                    add_to_history("assistant", f"Tool error: {e}")
                    return f"Tool execution failed for '{tool_name}': {e}"
            else:
                # Tool not found
                messages.append({
                    "role": "assistant",
                    "content": msg
                })
                messages.append({
                    "role": "user",
                    "content": f"[SYSTEM DIRECTIVE]: Tool '{tool_name}' does not exist. Please respond to the user in natural language."
                })
                tool_calls += 1
                continue

        # Check if model STILL returned raw JSON (or loop exhausted without natural language)
        final_check = parse_tool_call(msg)
        if final_check or (msg.strip().startswith("{") and "tool" in msg):
            if last_tool_result is not None:
                msg = format_fallback_response(last_tool_name, last_tool_args, last_tool_result)
            else:
                msg = "Sir, I have processed your request."

        # -------- FINAL HUMAN RESPONSE -------- #
        add_to_history("user", prompt)
        add_to_history("assistant", msg)

        # Auto-extract memories in background thread (non-blocking)
        try:
            import threading
            threading.Thread(
                target=auto_extract_memories,
                args=(prompt, msg),
                daemon=True
            ).start()
        except Exception:
            pass

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
