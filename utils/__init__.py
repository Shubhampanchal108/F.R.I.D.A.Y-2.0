"""
F.R.I.D.A.Y Utilities Package
=============================
Common system helpers, JSON cleansers, memory loaders, and database paths.
"""

from utils.helpers import (
    load_memory,
    save_memory,
    add_to_history,
    clean_json_string,
    normalize_role,
    parse_tool_call,
    search,
)
from utils.paths import (
    get_base_dir,
    BASE_DIR,
    DB_PATH,
    CHATS_PATH,
    CONTENT_PATH,
    AUDIO_PATH,
    DOCS_PATH,
    RAG_PATH,
    ALL_PATHS,
)

__all__ = [
    "load_memory",
    "save_memory",
    "add_to_history",
    "clean_json_string",
    "normalize_role",
    "parse_tool_call",
    "search",
    "get_base_dir",
    "BASE_DIR",
    "DB_PATH",
    "CHATS_PATH",
    "CONTENT_PATH",
    "AUDIO_PATH",
    "DOCS_PATH",
    "RAG_PATH",
    "ALL_PATHS",
]
