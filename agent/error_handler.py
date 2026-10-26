"""
=============================================================================
F.R.I.D.A.Y 2.0 // AUTONOMOUS AGENT ERROR DIAGNOSTICS & RECOVERY
=============================================================================
Analyzes tool execution and verification errors, determines recovery decisions
(Retry, Skip, Replan, Abort), and formulates targeted parameter fixes.
Uses the centralized multi-model router for resilient error analysis.
=============================================================================
"""

import json
import re
import os
import sys
from enum import Enum

# Parent imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.llm_router import chat_complete


class ErrorDecision(Enum):
    RETRY  = "retry"
    SKIP   = "skip"
    REPLAN = "replan"
    ABORT  = "abort"


ERROR_ANALYST_PROMPT = """You are the Error Diagnostics Engine of F.R.I.D.A.Y 2.0, Shubham sir's loyal personal AI secretary.
A step in an autonomous plan has encountered an issue or verification failed.
Analyze the failed step and determine the most intelligent course of recovery.

DECISION OPTIONS:
- retry   : Transient glitch (network timeout, temporary file lock). Retrying can work.
- skip    : Non-critical step (e.g. optional notification or status peek). Goal can succeed without it.
- replan  : The approach or tool was not optimal. A different tool or revised route must be taken.
- abort   : Fatal security or logical impossibility. Cannot safely continue.

Provide:
1. decision (retry | skip | replan | abort)
2. reason (short technical reason)
3. fix_suggestion (what to adjust)
4. user_message (A calm, natural, executive sentence that a human personal secretary would briefly say, <= 10 words, e.g. 'Adjusting the approach for this step, Sir.')

OUTPUT FORMAT (STRICT JSON ONLY):
{
  "decision": "retry|skip|replan|abort",
  "reason": "why it failed",
  "fix_suggestion": "what to change",
  "user_message": "Calm, natural secretary update"
}
"""


def analyze_error(
    step: dict,
    error: str,
    attempt: int = 1,
    max_attempts: int = 2
) -> dict:
    """
    Evaluates step failure and selects recovery path.
    """
    err_low = error.lower()

    # Fast path for common transient network errors
    if attempt < max_attempts and any(k in err_low for k in ["timeout", "timed out", "connection reset", "temporarily unavailable"]):
        return {
            "decision": ErrorDecision.RETRY,
            "reason": "Network or process timeout",
            "fix_suggestion": "Retry with slight delay",
            "user_message": "Retrying connection, Sir."
        }

    # If already tried max attempts, force replan
    if attempt >= max_attempts:
        return {
            "decision": ErrorDecision.REPLAN,
            "reason": f"Step reached maximum attempts: {error[:80]}",
            "fix_suggestion": "Switch to alternative approach",
            "user_message": "One moment Sir, switching the approach for this."
        }

    # If step is non-critical and failed
    if not step.get("critical", True) and attempt >= 1:
        return {
            "decision": ErrorDecision.SKIP,
            "reason": "Non-critical step failed; bypassing to keep moving",
            "fix_suggestion": "Skip to subsequent steps",
            "user_message": "Moving forward to the next step, Sir."
        }

    # LLM-based error reasoning via resilient router
    try:
        prompt = f"""Failed Step:
Step: {step.get('step')}
Tool: {step.get('tool')}
Description: {step.get('description')}
Parameters: {json.dumps(step.get('parameters', {}))}
Error Encountered: {error}
Attempt Number: {attempt} of {max_attempts}"""

        messages = [
            {"role": "system", "content": ERROR_ANALYST_PROMPT},
            {"role": "user", "content": prompt}
        ]

        raw_text = chat_complete(
            messages=messages,
            temperature=0.1,
            timeout=15.0
        )

        match = re.search(r"\{[\s\S]*\}", raw_text)
        data = json.loads(match.group() if match else raw_text)

        raw_dec = data.get("decision", "replan").lower().strip()
        dec_map = {
            "retry": ErrorDecision.RETRY,
            "skip": ErrorDecision.SKIP,
            "replan": ErrorDecision.REPLAN,
            "abort": ErrorDecision.ABORT
        }
        decision = dec_map.get(raw_dec, ErrorDecision.REPLAN)

        return {
            "decision": decision,
            "reason": data.get("reason", "Analysis completed"),
            "fix_suggestion": data.get("fix_suggestion", ""),
            "user_message": data.get("user_message", "Adjusting the approach, Sir.")
        }

    except Exception:
        # Safe default
        return {
            "decision": ErrorDecision.REPLAN,
            "reason": f"Execution error: {error[:80]}",
            "fix_suggestion": "Replan remaining task steps",
            "user_message": "One moment Sir, adjusting the plan."
        }


def generate_fix(step: dict, error: str, attempt: int) -> dict:
    """
    Attempts to mutate or sanitize step parameters based on the error.
    """
    params = dict(step.get("parameters", {}))

    # Common path / file name cleanups
    if "filename" in params:
        fn = str(params["filename"])
        clean_fn = re.sub(r'[\\/*?:"<>|]', "", os.path.basename(fn))
        if not clean_fn.endswith((".txt", ".md", ".py", ".json", ".csv")):
            clean_fn += ".txt"
        params["filename"] = clean_fn

    # Clean URL parameters
    if "url" in params:
        u = str(params["url"]).strip()
        if not u.startswith("http://") and not u.startswith("https://"):
            params["url"] = "https://" + u

    return params
