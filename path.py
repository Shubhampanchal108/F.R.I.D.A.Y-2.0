import os
import sys

def get_base_dir():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    appdata = os.getenv("LOCALAPPDATA")
    if appdata:
        base_dir = os.path.join(appdata, "Friday")

    os.makedirs(base_dir, exist_ok=True)
    return base_dir


# Base dir
BASE_DIR = get_base_dir()

# Main DB folder
DB_PATH = os.path.join(BASE_DIR, "Database")

# Subfolders
CHATS_PATH = os.path.join(DB_PATH, "chats")
CONTENT_PATH = os.path.join(DB_PATH, "content")
AUDIO_PATH = os.path.join(DB_PATH, "audio")
DOCS_PATH = os.path.join(DB_PATH, "docs")
RAG_PATH = os.path.join(DB_PATH, "memory")

# Create all folders
ALL_PATHS = [
    DB_PATH,
    CHATS_PATH,
    CONTENT_PATH,
    AUDIO_PATH,
    DOCS_PATH,
    RAG_PATH
]

for path in ALL_PATHS:
    os.makedirs(path, exist_ok=True)
