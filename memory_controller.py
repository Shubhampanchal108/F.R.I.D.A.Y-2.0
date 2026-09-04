import json
import os
import re
from datetime import datetime, timezone
from path import DOCS_PATH
from RAG import save_longterm_memory, search_vector_memory


PROFILE_FILE = os.path.join(DOCS_PATH, "user_profile.json")
SESSION_FILE = os.path.join(DOCS_PATH, "last_session.json")


# ================================================================
# AUTO-MEMORY EXTRACTION
# ================================================================

def auto_extract_memories(user_msg: str, assistant_reply: str):
    """
    After each conversation turn, use the LLM to extract memorable facts
    and save them automatically — no user action needed.
    This is the single biggest upgrade over the old manual-only memory.
    """
    # Skip trivial exchanges (greetings, short replies)
    if len(user_msg.strip()) < 15 or len(assistant_reply.strip()) < 15:
        return []

    # Skip tool-call-only responses (no human content to extract)
    if '"tool"' in assistant_reply and len(assistant_reply) < 100:
        return []

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

        extraction_prompt = f"""Analyze this conversation exchange and extract any facts worth remembering long-term about the user.
Look for: preferences, personal facts, instructions, relationships, habits, emotions, goals, opinions.

User said: "{user_msg}"
Assistant replied: "{assistant_reply}"

Rules:
- Only extract genuinely important/useful information
- If nothing is worth remembering, return an empty array []
- Return ONLY a valid JSON array, no other text
- Each item must have: "text", "type" (one of: preference, fact, instruction, relationship, habit, emotion, goal), "importance" (low/medium/high)

Example output:
[{{"text": "User prefers dark mode for coding", "type": "preference", "importance": "medium"}}]

Output:"""

        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0.1,
            timeout=10.0
        )

        result = response.choices[0].message.content.strip()

        # Parse JSON array from response
        match = re.search(r'\[[\s\S]*\]', result)
        if not match:
            return []

        memories = json.loads(match.group())

        if not isinstance(memories, list):
            return []

        saved = []
        for mem in memories:
            if isinstance(mem, dict) and "text" in mem:
                save_longterm_memory(
                    text=mem["text"],
                    memory_type=mem.get("type", "fact"),
                    tags=[mem.get("type", "auto_extracted")],
                    importance=mem.get("importance", "medium"),
                    source="auto_extract"
                )
                saved.append(mem["text"])

        # Also update the structured user profile
        if saved:
            _update_user_profile(memories)

        return saved

    except Exception as e:
        # Silently fail — auto-extraction is best-effort, never blocks the user
        print(f"⚠️ Auto-memory extraction error: {e}")
        return []


# ================================================================
# SESSION MANAGEMENT (Episodic Memory)
# ================================================================

def save_session_summary(conversation_history: list):
    """
    Generate and save a summary of the current session as episodic memory.
    Called on exit — enables cross-session continuity.
    """
    if not conversation_history or len(conversation_history) < 4:
        return None  # Too short to summarize

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

        # Build conversation text from last 30 messages
        conv_text = ""
        for msg in conversation_history[-30:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")[:200]  # Truncate long messages
            conv_text += f"{role}: {content}\n"

        summary_prompt = f"""Summarize this conversation session in 2-3 sentences.
Focus on: what the user was working on, key decisions made, any pending tasks or unfinished work.
Keep it concise and factual.

Conversation:
{conv_text}

Summary:"""

        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.2,
            timeout=10.0
        )

        summary = response.choices[0].message.content.strip()

        # Save as episodic memory in vector store
        save_longterm_memory(
            text=f"Session ({datetime.now().strftime('%Y-%m-%d %H:%M')}): {summary}",
            memory_type="episode",
            tags=["session_summary"],
            importance="high",
            source="session_end"
        )

        # Save last session info as JSON for fast cross-session greeting
        session_info = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "message_count": len(conversation_history)
        }

        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(session_info, f, indent=2, ensure_ascii=False)

        return summary

    except Exception as e:
        print(f"⚠️ Session summary error: {e}")
        return None


def get_last_session_context():
    """Get context from the last session for cross-session continuity greeting."""
    try:
        if not os.path.exists(SESSION_FILE):
            return None

        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            session_info = json.load(f)

        return session_info.get("summary", None)
    except Exception:
        return None


# ================================================================
# USER PROFILE (Semantic Memory — Dynamic Learning)
# ================================================================

def _load_user_profile():
    """Load the dynamic user profile."""
    default_profile = {
        "preferences": {},
        "facts": {},
        "relationships": {},
        "habits": {},
        "goals": [],
        "last_updated": ""
    }

    if not os.path.exists(PROFILE_FILE):
        os.makedirs(os.path.dirname(PROFILE_FILE), exist_ok=True)
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(default_profile, f, indent=2)
        return default_profile

    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return default_profile


def _save_user_profile(profile):
    """Save the dynamic user profile."""
    profile["last_updated"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(PROFILE_FILE), exist_ok=True)
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)


def _update_user_profile(memories: list):
    """Update user profile with extracted memories."""
    try:
        profile = _load_user_profile()

        for mem in memories:
            if not isinstance(mem, dict):
                continue

            mem_type = mem.get("type", "fact")
            text = mem.get("text", "")
            key = text[:60]  # Use truncated text as key

            if mem_type == "preference":
                profile["preferences"][key] = text
            elif mem_type == "fact":
                profile["facts"][key] = text
            elif mem_type == "relationship":
                profile["relationships"][key] = text
            elif mem_type == "habit":
                profile["habits"][key] = text
            elif mem_type == "goal":
                if text not in profile["goals"]:
                    profile["goals"].append(text)
                    profile["goals"] = profile["goals"][-20:]  # Keep last 20

        _save_user_profile(profile)
    except Exception as e:
        print(f"⚠️ Profile update error: {e}")


def get_user_profile_summary():
    """Get a formatted summary of the user profile for LLM context injection."""
    try:
        profile = _load_user_profile()

        parts = []
        if profile.get("preferences"):
            prefs = list(profile["preferences"].values())[:5]
            parts.append("Preferences: " + "; ".join(prefs))

        if profile.get("facts"):
            facts = list(profile["facts"].values())[:5]
            parts.append("Known Facts: " + "; ".join(facts))

        if profile.get("goals"):
            goals = profile["goals"][:3]
            parts.append("Current Goals: " + "; ".join(goals))

        if profile.get("habits"):
            habits = list(profile["habits"].values())[:3]
            parts.append("Habits: " + "; ".join(habits))

        if profile.get("relationships"):
            rels = list(profile["relationships"].values())[:3]
            parts.append("Relationships: " + "; ".join(rels))

        return "\n".join(parts) if parts else ""
    except Exception:
        return ""


# ================================================================
# PROACTIVE MEMORY SURFACING
# ================================================================

def get_proactive_memories():
    """
    Check for memories that should be proactively surfaced.
    Called periodically by the daemon for time-based and context-based alerts.
    """
    try:
        now = datetime.now()
        time_queries = [
            f"reminder for {now.strftime('%A')} {now.strftime('%B %d')}",
            "deadline upcoming soon",
        ]

        proactive = []
        for query in time_queries:
            results = search_vector_memory(
                query, top_k=2,
                collections_to_search=["general", "facts"],
                apply_threshold=True
            )
            for mem in results:
                if mem.get("adjusted_distance", 999) < 0.8:  # Very high relevance only
                    proactive.append(mem)

        return proactive
    except Exception:
        return []
