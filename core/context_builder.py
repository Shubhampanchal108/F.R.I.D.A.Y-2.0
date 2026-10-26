"""
=============================================================================
F.R.I.D.A.Y 2.0 // COGNITIVE CONTEXT & MEMORY BUILDER
=============================================================================
Assembles full prompt context: conversation history, cross-session continuity,
user profile facts, vector long-term memories, and daemon sentinel alerts.
=============================================================================
"""

import os
import sys
from typing import List, Dict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import Friday_Instruction
from utils.helpers import load_memory, normalize_role
from memory.rag import search_vector_memory
from memory.memory_manager import get_last_session_context, get_user_profile_summary


def build_system_messages(prompt: str) -> List[Dict[str, str]]:
    """
    Constructs the base system context and message history for any LLM deliberation.
    """
    messages = [{"role": "system", "content": Friday_Instruction}]

    # 1. Previous conversation history
    try:
        memory = load_memory()
        history = memory.get("conversation_history", [])
        for m in history:
            messages.append({
                "role": normalize_role(m.get("role", "user")),
                "content": m.get("content", "")
            })
    except Exception:
        pass

    # 2. Cross-session continuity
    try:
        last_session = get_last_session_context()
        if last_session:
            messages.append({
                "role": "system",
                "content": f"[LAST SESSION CONTEXT] {last_session}"
            })
    except Exception:
        pass

    # 3. Dynamic user profile
    try:
        profile_summary = get_user_profile_summary()
        if profile_summary:
            messages.append({
                "role": "system",
                "content": f"[USER PROFILE]\n{profile_summary}"
            })
    except Exception:
        pass

    # 4. Long-term vector memory retrieval
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
                "content": f"[MEMORY CONTEXT] Relevant memories about user:\n{memories_str}"
            })
    except Exception:
        pass

    # 5. Proactive sentinel awareness
    try:
        from services.daemon import daemon_instance
        recent_alerts = daemon_instance.get_recent_alerts(limit=5)
        if recent_alerts:
            alerts_summary = "\n".join([
                f"- [{a.get('timestamp', '')}] ({a.get('title', 'Alert')}): {a.get('message', '')}"
                for a in recent_alerts
            ])
            messages.append({
                "role": "system",
                "content": f"[RECENT PROACTIVE SPOKEN ALERTS GIVEN TO SHUBHAM SIR]\n{alerts_summary}"
            })
    except Exception:
        pass

    return messages
