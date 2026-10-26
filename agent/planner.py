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


def _get_planner_prompt() -> str:
    """Builds the planner prompt with available super-agent tools."""
    return f"""You are the Autonomous Planning Engine of F.R.I.D.A.Y 2.0, Shubham sir's AI Super-Agent.
Your job: Analyze any user goal and decompose it into an efficient, logical sequence of actionable steps using ONLY the available tools.
If the user's input is a general conversation, greeting, explanation question, or does NOT require computer tools, mark "is_conversational": true.

ABSOLUTE OPERATIONAL RULES:
1. Return ONLY valid JSON. Absolutely no markdown fences, no conversational banter, no commentary.
2. Use ONLY the available tools listed below.
3. Every step must be atomic and clear. Use minimum steps necessary (1 to 5 steps max).
4. If a step produces content that subsequent steps need (e.g. web search output -> save to file), the execution engine will automatically pipe the result context forward.
5. If the goal can be accomplished with a single direct tool, generate a 1-step plan.
6. Provide an intuitive description and specify `critical: true` for essential steps.
7. Include `verification_type` ("content", "file_exists", "status_ok", "none") so the executor can verify actual success.

AVAILABLE TOOLS AND PARAMETERS:

- google_search
    query: string (required) - focused search query
- extract_webpage_content
    url: string (required) - URL to scrape and extract text
- deep_research_agent
    topic: string (required) - comprehensive multi-source research topic
- read_pdf_or_document
    filepath: string (required) - path to PDF or document file to read
- create_and_open_file
    filename: string (required) - filename (e.g. 'ai_report.txt')
    content: string (required) - initial text content or placeholder
- update_file
    filename: string (required)
    new_content: string (required)
- read_file
    filename: string (required)
- list_files
- run_python_code
    code: string (required) - complete executable Python script
- code_reviewer_agent
    code_or_filename: string (required) - code snippet or filename
- open_app
    app: string (required) - application name (e.g. 'chrome', 'notepad', 'spotify')
- close_app
    app: string (optional)
- focus_window
    app_name: string (required)
- copy_to_clipboard
    text: string (required)
- get_clipboard_content
- add_task
    task_text: string (required)
- list_tasks
- add_reminder
    reminder_text: string (required)
    remind_at: string (required) - e.g. 'tomorrow at 9 AM', 'in 30 minutes'
- send_email
    to: string (required)
    subject: string (required)
    body: string (required)
- open_website
    url: string (required) - valid https URL
- get_weather
    city: string (required)
- check_battery
- check_cpu
- capture_screenshot
- analyze_screen
    prompt: string (required)

OUTPUT JSON FORMAT (STRICT):
{{
  "goal": "string",
  "is_conversational": false,
  "steps": [
    {{
      "step": 1,
      "tool": "tool_name",
      "description": "brief description of what this step does",
      "parameters": {{}},
      "verification_type": "content|file_exists|status_ok|none",
      "critical": true
    }}
  ]
}}
"""


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
