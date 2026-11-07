import time
import os
import sys
import json

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools.Emails import check_new_mail
from utils.paths import DOCS_PATH

SEEN_EMAILS_FILE = os.path.join(DOCS_PATH, "seen_emails.json")


class EmailSentinel:
    """
    Monitors incoming unread emails and alerts Shubham sir with sender and subject.
    Persists seen email IDs to disk so emails are never announced repeatedly.
    """

    def __init__(self, notifier, email_check_interval=60.0):
        self.notifier = notifier
        self._seen_email_ids = set()
        self._last_email_check = 0
        self.email_check_interval = email_check_interval
        self._load_seen_emails()

    def _load_seen_emails(self):
        try:
            if os.path.exists(SEEN_EMAILS_FILE):
                with open(SEEN_EMAILS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._seen_email_ids = set(data)
            else:
                # First run: prime with current unread email so existing inbox is not spammed
                initial_mail = check_new_mail(peek=True)
                if initial_mail and isinstance(initial_mail, dict):
                    m_id = str(initial_mail.get("id") or f"{initial_mail.get('sender')}_{initial_mail.get('subject')}")
                    self._seen_email_ids.add(m_id)
                    self._save_seen_emails()
        except Exception:
            pass

    def _save_seen_emails(self):
        try:
            os.makedirs(os.path.dirname(SEEN_EMAILS_FILE), exist_ok=True)
            with open(SEEN_EMAILS_FILE, "w", encoding="utf-8") as f:
                json.dump(list(self._seen_email_ids)[-200:], f, indent=2)
        except Exception:
            pass

    def check(self):
        now = time.time()
        if now - self._last_email_check < self.email_check_interval:
            return

        self._last_email_check = now
        try:
            new_mail = check_new_mail(peek=True)
            if new_mail and isinstance(new_mail, dict):
                mail_id = str(new_mail.get("id") or f"{new_mail.get('sender')}_{new_mail.get('subject')}")
                if mail_id not in self._seen_email_ids:
                    self._seen_email_ids.add(mail_id)
                    self._save_seen_emails()

                    sender = new_mail.get("sender", "Unknown Sender")
                    subject = new_mail.get("subject", "No Subject")

                    desktop_text = f"From: {sender}\nSubject: {subject}"
                    voice_text = f"Sir, you have received a new email from {sender}. Subject: {subject}."

                    self.notifier.announce(
                        "New Email Alert",
                        desktop_text,
                        voice_text,
                        event_type="incoming_email",
                        details={"sender": sender, "subject": subject}
                    )
        except Exception as e:
            self.notifier.log_event("Email Check Error", str(e), level="ERROR")


