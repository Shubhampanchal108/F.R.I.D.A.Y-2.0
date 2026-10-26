"""
=============================================================================
F.R.I.D.A.Y 2.0 // CORE TOOL EXECUTION ENGINE & SLAVE WORKER
=============================================================================
Executes atomic tool actions delegated by the Agent Controller.
100% silent execution: tools return pure status and raw results/errors.
Zero hardcoded speech. Response generation is driven dynamically by the Agent LLM.
=============================================================================
"""

import os
import sys
from typing import Callable, Any, Dict

# Ensure parent directory in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.tool_guard import load_tools, execute_tool, TOOLS
from utils.helpers import add_to_history

# Initialize tool registry
registry = load_tools()


def execute_action(tool_name: str, args: Dict[str, Any], origin: str = "server") -> Dict[str, Any]:
    """
    Executes a tool on behalf of the Agent Master.
    Returns structured success or error dictionary.
    No speech is spoken here.
    """
    if tool_name not in TOOLS:
        return {
            "status": "error",
            "tool": tool_name,
            "error": f"Tool '{tool_name}' is not recognized in the registry."
        }

    try:
        raw_result = execute_tool(tool_name=tool_name, origin=origin, **args)

        # Check for error indicators in return
        if isinstance(raw_result, dict) and raw_result.get("status") == "error":
            return {
                "status": "error",
                "tool": tool_name,
                "error": raw_result.get("message") or raw_result.get("error") or "Execution failed",
                "raw": raw_result
            }

        if isinstance(raw_result, str) and (raw_result.startswith("❌") or raw_result.startswith("🚫")):
            return {
                "status": "error",
                "tool": tool_name,
                "error": raw_result,
                "raw": raw_result
            }

        return {
            "status": "success",
            "tool": tool_name,
            "result": raw_result
        }

    except Exception as e:
        return {
            "status": "error",
            "tool": tool_name,
            "error": str(e)
        }


def Brain(prompt: str, origin: str = 'server', source: str = None, tool_callback: Callable = None, speak: Callable = None) -> str:
    """
    Primary Entry Point: Delegates every user query directly to the
    Agent Controller (Master) which plans, executes via Brain slave,
    and dynamically produces human responses with zero hardcoded speech.
    """
    if source is not None:
        origin = source

    from agent.executor import FridayAgentExecutor
    executor = FridayAgentExecutor()

    # Pass query to Agent Master
    response = executor.execute(
        goal=prompt,
        tool_callback=tool_callback,
        speak=speak,
        origin=origin
    )

    # Persist in conversation memory
    try:
        add_to_history("user", prompt)
        add_to_history("assistant", response)
    except Exception:
        pass

    return response
