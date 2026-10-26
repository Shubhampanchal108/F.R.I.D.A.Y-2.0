"""
F.R.I.D.A.Y Memory & Knowledge Package
======================================
Working memory controller, episodic session summarizer, and RAG vector store.
"""

from memory.memory_manager import (
    auto_extract_memories,
    get_last_session_context,
    get_user_profile_summary,
    save_session_summary,
    _update_user_profile,
)
from memory.rag import (
    save_longterm_memory,
    search_vector_memory,
    delete_memory_by_id,
    get_all_memories,
    COLLECTIONS,
)

delete_memory = delete_memory_by_id
list_all_memories = get_all_memories

__all__ = [
    "auto_extract_memories",
    "get_last_session_context",
    "get_user_profile_summary",
    "save_session_summary",
    "_update_user_profile",
    "save_longterm_memory",
    "search_vector_memory",
    "delete_memory_by_id",
    "delete_memory",
    "get_all_memories",
    "list_all_memories",
    "COLLECTIONS",
]
