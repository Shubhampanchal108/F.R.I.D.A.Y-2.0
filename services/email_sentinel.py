import time
import os
import sys

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools.Emails import check_new_mail


class EmailSentinel:
    """
    Monitors incoming unread emails and alerts Shubham sir with sender and subject.
    """

    def __init__(self, notifier, email_check_interval=45.0):
        self.notifier = notifier
        self._seen_email_ids = set()
        self._last_email_check = 0
        self.email_check_interval = email_check_interval

    def check(self):
        now = time.time()
        if now - self._last_email_check < self.email_check_interval:
            return

        self._last_email_check = now
        try:
            new_mail = check_new_mail(peek=True)
            if new_mail and isinstance(new_mail, dict):
                mail_id = new_mail.get("id") or f"{new_mail.get('sender')}_{new_mail.get('subject')}"
                if mail_id not in self._seen_email_ids:
                    self._seen_email_ids.add(mail_id)
                    if len(self._seen_email_ids) > 100:
                        self._seen_email_ids.pop()

                    sender = new_mail.get("sender", "Unknown Sender")
                    subject = new_mail.get("subject", "No Subject")

                    desktop_text = f"From: {sender}\nSubject: {subject}"
                    voice_text = f"Sir, you have received a new email from {sender}. The subject is: {subject}."

                    self.notifier.announce(
                        "New Email Alert",
                        desktop_text,
                        voice_text,
                        event_type="incoming_email",
                        details={"sender": sender, "subject": subject}
                    )
        except Exception as e:
            self.notifier.log_event("Email Check Error", str(e), level="ERROR")

