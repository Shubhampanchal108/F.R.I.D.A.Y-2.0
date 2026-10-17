"""
F.R.I.D.A.Y // Clipboard Controller Tool
Copies text/code to clipboard and retrieves clipboard content.
"""

import pyperclip


def copy_to_clipboard(text: str) -> dict:
    """
    Copies the given text or code snippet directly into the Windows clipboard.
    Allows Shubham sir to immediately paste with Ctrl + V.
    """
    try:
        if text is None:
            text = ""
        pyperclip.copy(str(text))
        preview = str(text)[:60] + ("..." if len(str(text)) > 60 else "")
        return {
            "status": "success",
            "action": "copy_to_clipboard",
            "message": "Content successfully copied to clipboard, Sir.",
            "preview": preview,
            "characters_copied": len(str(text))
        }
    except Exception as e:
        return {
            "status": "error",
            "action": "copy_to_clipboard",
            "message": f"Failed to copy to clipboard: {str(e)}"
        }


def get_clipboard_content() -> dict:
    """
    Retrieves the current text content from the Windows clipboard.
    """
    try:
        content = pyperclip.paste()
        if not content:
            return {
                "status": "success",
                "message": "Clipboard is currently empty.",
                "content": ""
            }
        return {
            "status": "success",
            "action": "get_clipboard_content",
            "content": content,
            "length": len(content)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to read clipboard: {str(e)}"
        }
