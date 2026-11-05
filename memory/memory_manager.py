import json
import os
import re
from datetime import datetime, timezone
from utils.paths import DOCS_PATH
from memory.rag import save_longterm_memory, search_vector_memory


PROFILE_FILE = os.path.join(DOCS_PATH, "user_profile.json")
SESSION_FILE = os.path.join(DOCS_PATH, "last_session.json")


# ================================================================
# AUTO-MEMORY EXTRACTION
# ================================================================

def auto_extract_memories(user_msg: str, assistant_reply: str):
    """
    After each conversation turn, extract memorable facts and contact info
    and save them automatically to both vector store and user profile.
    """
    u_clean = user_msg.strip()
    if not u_clean or len(u_clean) < 4:
        return []

    saved = []

    # 1. Immediate Instant Deterministic Extraction for Family, Contacts, and Personal Info
    u_lower = u_clean.lower()
    contact_keywords = [
        "mummy", "mother", "maa", "mom", "papa", "father", "dad", "bhai", "brother",
        "behan", "sister", "dost", "friend", "email", "mail", "phone", "mobile",
        "contact", "number", "no", "yaad rakh", "remember", "mera", "meri", "birthday"
    ]
    if any(k in u_lower for k in contact_keywords):
        detected_text = u_clean
        # Strip common instruction prefixes like 'friday yaad rakhna'
        for prefix in ["friday yaad rakhna", "yaad rakhna", "remember that", "remember", "note down", "please remember"]:
            if u_lower.startswith(prefix):
                detected_text = u_clean[len(prefix):].lstrip(" ,:-").strip()
                break

        mem_type = "relationship" if any(r in u_lower for r in ["mummy", "mother", "maa", "mom", "papa", "father", "bhai", "sister"]) else "fact"
        save_longterm_memory(
            text=detected_text,
            memory_type=mem_type,
            tags=[mem_type, "contact_info", "critical_user_fact"],
            importance="critical",
            source="user_direct"
        )
        _update_user_profile([{"text": detected_text, "type": mem_type, "importance": "critical"}])
        saved.append(detected_text)

    # 2. LLM Deliberation for In-Depth Facts and Preferences
    try:
        from core.llm_router import chat_complete

        extraction_prompt = f"""Analyze this conversation turn and extract any facts, contacts, numbers, relationships, or preferences worth remembering long-term about the user.
User said: "{user_msg}"
Assistant replied: "{assistant_reply}"

Rules:
- Extract facts, personal contacts (e.g. mother's phone, email), preferences, and habits.
- Return ONLY a valid JSON array like:
  [{{"text": "Mummy's phone number is 9876543210", "type": "relationship", "importance": "critical"}}]
- If nothing worth remembering, return []"""

        messages = [{"role": "user", "content": extraction_prompt}]
        response_text = chat_complete(messages=messages, temperature=0.1, timeout=8.0)

        match = re.search(r'\[[\s\S]*\]', response_text)
        if match:
            memories = json.loads(match.group())
            if isinstance(memories, list):
                for mem in memories:
                    if isinstance(mem, dict) and "text" in mem:
                        t = mem["text"]
                        if t not in saved:
                            m_type = mem.get("type", "fact")
                            imp = mem.get("importance", "high")
                            save_longterm_memory(
                                text=t,
                                memory_type=m_type,
                                tags=[m_type, "auto_extracted"],
                                importance=imp,
                                source="auto_extract"
                            )
                            saved.append(t)
                if memories:
                    _update_user_profile(memories)

    except Exception as e:
        pass

    return saved


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
        from core.llm_router import chat_complete

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

        summary = chat_complete(
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.2,
            timeout=15.0
        ).strip()

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
        if profile.get("relationships"):
            rels = list(profile["relationships"].values())[:20]
            parts.append("Family & Relationships (Crucial Contacts):\n- " + "\n- ".join(rels))

        if profile.get("facts"):
            facts = list(profile["facts"].values())[:25]
            parts.append("Known Facts & Personal Details:\n- " + "\n- ".join(facts))

        if profile.get("preferences"):
            prefs = list(profile["preferences"].values())[:10]
            parts.append("Preferences: " + "; ".join(prefs))

        if profile.get("goals"):
            goals = profile["goals"][:5]
            parts.append("Current Goals: " + "; ".join(goals))

        if profile.get("habits"):
            habits = list(profile["habits"].values())[:5]
            parts.append("Habits: " + "; ".join(habits))

        return "\n\n".join(parts) if parts else ""
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
