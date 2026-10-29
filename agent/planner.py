"""
=============================================================================
F.R.I.D.A.Y 2.0 // AUTONOMOUS AGENT GOAL PLANNER
=============================================================================
Breaks high-level user directives into structured, verified actionable steps.
Dynamically respects user Settings (e.g. Computer-Use toggle).
Integrates directly with the multi-model LLM router for 100% quota resilience.
=============================================================================
"""

import json
import re
import os
import sys

# Ensure parent directory imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.llm_router import chat_complete
from config.planner_prompt import PLANNER_AGENT_PROMPT


def _get_planner_prompt() -> str:
    """Builds the planner prompt with available super-agent tools."""
    return PLANNER_AGENT_PROMPT


def _clean_json_text(text: str) -> str:
    """Strip markdown code blocks or surrounding whitespace."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def create_plan(goal: str, context: str = "") -> dict:
    """
    Deconstructs a user goal into an executable multi-step verified plan.
    """
    user_prompt = f"Goal: {goal}"
    if context:
        user_prompt += f"\n\nContext / User Profile:\n{context}"

    messages = [
        {"role": "system", "content": _get_planner_prompt()},
        {"role": "user", "content": user_prompt}
    ]

    try:
        raw_text = chat_complete(
            messages=messages,
            temperature=0.2,
            timeout=25.0
        )

        cleaned = _clean_json_text(raw_text)
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            plan = json.loads(match.group())
        else:
            plan = json.loads(cleaned)

        if not isinstance(plan, dict):
            raise ValueError("Plan is not a valid JSON dictionary")

        if plan.get("is_conversational"):
            return plan

        if "steps" not in plan or not isinstance(plan["steps"], list):
            raise ValueError("Plan JSON missing valid 'steps' list")

        print(f"[Friday Planner] ✅ Prepared {len(plan['steps'])}-step verified plan for: '{goal[:60]}'")
        for s in plan["steps"]:
            print(f"   [Step {s.get('step')}] -> {s.get('tool')}: {s.get('description')}")

        return plan

    except Exception as e:
        print(f"[Friday Planner] ⚠️ Planner generation note: {e} — constructing adaptive fallback plan")
        return _create_fallback_plan(goal)


def replan(goal: str, completed_steps: list, failed_step: dict, error: str) -> dict:
    """
    Generates a revised plan when an execution step fails.
    Preserves successfully completed steps and only formulates alternative steps for the remainder.
    """
    completed_summary = "\n".join([
        f"- Step {s.get('step')} [{s.get('tool')}]: COMPLETED ({s.get('description')})"
        for s in completed_steps
    ]) if completed_steps else "None"

    replan_prompt = f"""User Goal: {goal}

COMPLETED STEPS (DO NOT REPEAT THESE):
{completed_summary}

FAILED STEP:
Tool: {failed_step.get('tool')}
Description: {failed_step.get('description')}
Parameters: {json.dumps(failed_step.get('parameters', {}))}
Error Encountered: {error}

TASK:
Formulate a REVISED plan to achieve the remaining portion of the goal.
Do NOT repeat successfully completed steps.
Use alternative tools or revised parameters to bypass the roadblock.
Return ONLY valid JSON matching the strict format."""

    messages = [
        {"role": "system", "content": _get_planner_prompt()},
        {"role": "user", "content": replan_prompt}
    ]

    try:
        raw_text = chat_complete(
            messages=messages,
            temperature=0.2,
            timeout=25.0
        )

        cleaned = _clean_json_text(raw_text)
        match = re.search(r"\{[\s\S]*\}", cleaned)
        plan = json.loads(match.group() if match else cleaned)

        print(f"[Friday Planner] 🔄 Dynamically revised plan generated ({len(plan.get('steps', []))} remaining steps)")
        return plan

    except Exception as e:
        print(f"[Friday Planner] ⚠️ Replanning note: {e} — constructing adaptive fallback plan")
        return _create_fallback_plan(goal)


def _create_fallback_plan(goal: str) -> dict:
    """Direct single-step fallback plan."""
    g_lower = goal.lower()
    if any(k in g_lower for k in ["search", "who is", "what is", "news", "price", "tell me about"]):
        tool = "google_search"
        params = {"query": goal}
    elif any(k in g_lower for k in ["write code", "calculate", "math", "script"]):
        tool = "run_python_code"
        params = {"code": f"# Task: {goal}\nprint('Executing task')"}
    elif any(k in g_lower for k in ["email", "mail", "send_email"]):
        tool = "send_email"
        params = {"to": "", "subject": "Update", "body": goal}
    elif any(k in g_lower for k in ["battery", "charge", "power"]):
        tool = "check_battery"
        params = {}
    elif any(k in g_lower for k in ["cpu", "ram", "memory"]):
        tool = "check_cpu"
        params = {}
    elif any(k in g_lower for k in ["weather", "temperature", "forecast"]):
        tool = "get_weather"
        params = {"city": "Delhi"}
    else:
        return {
            "goal": goal,
            "is_conversational": True,
            "steps": []
        }

    return {
        "goal": goal,
        "is_conversational": False,
        "steps": [
            {
                "step": 1,
                "tool": tool,
                "description": f"Handle objective: {goal[:50]}",
                "parameters": params,
                "verification_type": "status_ok",
                "critical": True
            }
        ]
    }


if __name__ == "__main__":
    str = input("Enter you prompt: ")
    print(PLANNER_AGENT_PROMPT)