import time
import os
import sys

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class ClipboardSentinel:
    """
    Autonomous code error & traceback monitor for user clipboard.
    Proactively detects Python errors and offers immediate diagnosis.
    """

    TRACEBACK_INDICATORS = [
        "traceback (most recent call last):",
        "syntaxerror:",
        "nameerror:",
        "typeerror:",
        "indexerror:",
        "valueerror:",
        "attributeerror:",
        "modulenotfounderror:",
        "zerodivisionerror:",
        "keyerror:"
    ]

    def __init__(self, notifier, cooldown=25.0):
        self.notifier = notifier
        self._last_clipboard_text = ""
        self._last_clipboard_time = 0
        self.cooldown = cooldown

    def check(self):
        """Proactively monitors user clipboard for tracebacks, code errors, or actionable links."""
        try:
            import pyperclip
            text = pyperclip.paste()
            if not text or not isinstance(text, str):
                return

            text = text.strip()
            if len(text) < 15 or text == self._last_clipboard_text:
                return

            self._last_clipboard_text = text
            now = time.time()
            if now - self._last_clipboard_time < self.cooldown:
                return

            text_lower = text.lower()
            if any(ind in text_lower for ind in self.TRACEBACK_INDICATORS):
                self._last_clipboard_time = now
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                err_type = lines[-1] if lines else "Python Traceback"
                title = "Code Error Detected in Clipboard"
                desktop_msg = f"Observed traceback: {err_type[:60]}\nSay: 'Friday, fix clipboard error' to solve."
                voice_msg = f"Sir, I noticed a code traceback in your clipboard: {err_type[:50]}. You can say 'Friday, fix clipboard error' and I will diagnose it for you."
                self.notifier.announce(
                    title,
                    desktop_msg,
                    voice_msg,
                    event_type="clipboard_code_traceback",
                    details={"error_summary": err_type[:60]}
                )
        except Exception:
            pass

