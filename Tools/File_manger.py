import os
from datetime import datetime
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from path import CONTENT_PATH


# ==============================
# CONFIG
# ==============================

BASE_DIR = CONTENT_PATH
os.makedirs(BASE_DIR, exist_ok=True)

# ==============================
# UTILITY
# ==============================

def _file_path(filename):
    return os.path.join(BASE_DIR, filename)


def _response_success(action, message, extra=None):
    data = {
        "status": "success",
        "action": action,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    if extra:
        data.update(extra)
    return data


def _response_error(code, message):
    return {
        "status": "error",
        "code": code,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

# ==============================
# CREATE FILE
# ==============================


def create_and_open_file(filename, content):
    try:
        path = os.path.join(BASE_DIR, filename)

        if os.path.exists(path):
            return {
                "status": "error",
                "code": "FILE_ALREADY_EXISTS",
                "message": f"{filename} already exists"
            }

        # Create file
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        # Auto open file (Windows)
        os.startfile(path)

        return {
            "status": "success",
            "action": "create_and_open_file",
            "message": "File created and opened successfully",
            "file": filename,
            "path": path,
            "opened": True,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "FILE_CREATE_OPEN_FAILED",
            "message": str(e)
        }


# ==============================
# READ FILE
# ==============================

def read_file(filename):
    try:
        path = _file_path(filename)

        if not os.path.exists(path):
            return _response_error(
                "FILE_NOT_FOUND",
                f"{filename} does not exist"
            )

        # Read content
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Auto open file (Windows)
        os.startfile(path)

        return _response_success(
            "read_file",
            "File read and opened successfully",
            {
                "file": filename,
                "content": content,
                "opened": True,
                "path": path
            }
        )

    except Exception as e:
        return _response_error("FILE_READ_OPEN_FAILED", str(e))
# ==============================
# UPDATE FILE
# ==============================


def update_file(filename, new_content):
    try:
        path = _file_path(filename)

        if not os.path.exists(path):
            return _response_error(
                "FILE_NOT_FOUND",
                f"{filename} does not exist"
            )

        # Update content
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

        # Auto open updated file (Windows)
        os.startfile(path)

        return _response_success(
            "update_file",
            "File updated and opened successfully",
            {
                "file": filename,
                "opened": True,
                "path": path
            }
        )

    except Exception as e:
        return _response_error("FILE_UPDATE_OPEN_FAILED", str(e))

# ==============================
# DELETE FILE
# ==============================

def delete_file(filename):
    try:
        path = _file_path(filename)

        if not os.path.exists(path):
            return _response_error(
                "FILE_NOT_FOUND",
                f"{filename} does not exist"
            )

        os.remove(path)

        return _response_success(
            "delete_file",
            "File deleted successfully",
            {"file": filename}
        )

    except Exception as e:
        return _response_error("FILE_DELETE_FAILED", str(e))


# ==============================
# LIST FILES
# ==============================

def list_files():
    try:
        files = os.listdir(BASE_DIR)

        return _response_success(
            "list_files",
            "Files fetched successfully",
            {"count": len(files), "files": files}
        )

    except Exception as e:
        return _response_error("FILE_LIST_FAILED", str(e))


# ==============================
# RENAME FILE
# ==============================

def rename_file(old_name, new_name):
    try:
        old_path = _file_path(old_name)
        new_path = _file_path(new_name)

        if not os.path.exists(old_path):
            return _response_error(
                "FILE_NOT_FOUND",
                f"{old_name} does not exist"
            )

        if os.path.exists(new_path):
            return _response_error(
                "FILE_ALREADY_EXISTS",
                f"{new_name} already exists"
            )

        os.rename(old_path, new_path)

        return _response_success(
            "rename_file",
            "File renamed successfully",
            {"old_name": old_name, "new_name": new_name}
        )

    except Exception as e:
        return _response_error("FILE_RENAME_FAILED", str(e))


# ==============================
# SEARCH FILE CONTENT
# ==============================

def search_in_file(filename, keyword):
    try:
        path = _file_path(filename)

        if not os.path.exists(path):
            return _response_error(
                "FILE_NOT_FOUND",
                f"{filename} does not exist"
            )

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        matches = content.lower().count(keyword.lower())

        return _response_success(
            "search_in_file",
            "Search completed",
            {
                "file": filename,
                "keyword": keyword,
                "matches": matches
            }
        )

    except Exception as e:
        return _response_error("FILE_SEARCH_FAILED", str(e))


# ==============================
# SEARCH FILE
# ==============================

def search_file_in_folder(filename):
    try:
        path = _file_path(filename)

        exists = os.path.exists(path)

        return _response_success(
            "search_file_in_folder",
            "File search completed",
            {
                "file": filename,
                "exists": exists,
                "path": path if exists else None
            }
        )

    except Exception as e:
        return _response_error("FILE_SEARCH_FAILED", str(e))


# ==============================
# TEST MODE
# ==============================

if __name__ == "__main__":
    print(create_and_open_file("demo.txt", "Hello Friday ❤️"))
    print(read_file("demo.txt"))
    print(update_file("demo.txt", "Updated by Friday 🤖"))
    print(search_in_file("demo.txt", "friday"))
    print(list_files())
    print(rename_file("demo.txt", "final.txt"))
    # print(delete_file("final.txt"))
