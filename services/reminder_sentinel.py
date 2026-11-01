import os
import sys

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools.reminder import get_due_reminders


class ReminderSentinel:
    """
    Monitors due reminders and surfaces time-relevant long-term memories.
    """

    def __init__(self, notifier):
        self.notifier = notifier

    def check_due_reminders(self):
        try:
            due = get_due_reminders()
            if due:
                for reminder in due:
                    title = "Reminder Alert"
                    msg = f"Sir, you asked me to remind you: '{reminder}'"
                    self.notifier.announce(
                        title,
                        msg,
                        msg,
                        event_type="reminder_due",
                        details={"reminder": reminder}
                    )
        except Exception as e:
            self.notifier.log_event("Reminder Check Error", str(e), level="ERROR")

    def check_proactive_memories(self):
        """Periodically check for time-relevant memories to surface proactively."""
        try:
            from memory.memory_manager import get_proactive_memories
            memories = get_proactive_memories()
            for mem in memories:
                text = mem.get("text", "")
                if text:
                    self.notifier.announce(
                        "Memory Recall",
                        f"Sir, I recall something relevant: {text[:120]}",
                        f"Sir, I recall something relevant to your schedule: {text[:120]}"
                    )
        except Exception as e:
            self.notifier.log_event("Memory Surfacing Error", str(e), level="ERROR")

