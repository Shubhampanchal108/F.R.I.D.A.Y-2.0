import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import re

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")


def decode_text(text):
    if text is None:
        return ""
    decoded, charset = decode_header(text)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(charset or "utf-8", errors="ignore")
    return decoded


def read_latest_emails(n=5):
    mail = None
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        status, data = mail.search(None, "ALL")

        if status != "OK":
            return {
                "status": "error",
                "message": "Failed to search inbox",
                "emails": []
            }

        ids = data[0].split()

        if not ids:
            return {
                "status": "success",
                "message": "Inbox is empty",
                "emails": []
            }

        latest_ids = ids[-n:]

        emails_list = []

        for i in latest_ids:
            status, msg_data = mail.fetch(i, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(msg_data[0][1])

            subject = decode_text(msg.get("Subject"))
            sender = decode_text(msg.get("From"))

            emails_list.append({
                "from": sender,
                "subject": subject
            })

        return {
            "status": "success",
            "message": f"Fetched {len(emails_list)} emails",
            "emails": emails_list
        }

    except imaplib.IMAP4.error as e:
        return {
            "status": "error",
            "message": f"IMAP error: {str(e)}",
            "emails": []
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "emails": []
        }

    finally:
        try:
            if mail:
                mail.logout()
        except:
            pass


#send Mail
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)


def send_email(to, subject, body):
    server = None

    # ---------- Credential Check ----------
    if not EMAIL or not PASSWORD:
        return {
            "status": "error",
            "code": "CREDENTIALS_MISSING",
            "message": "Email or password not found in environment variables"
        }

    # ---------- Input Validation ----------
    if not to or not is_valid_email(to):
        return {
            "status": "error",
            "code": "INVALID_RECIPIENT",
            "message": "Invalid recipient email address"
        }

    if not subject or not body:
        return {
            "status": "error",
            "code": "EMPTY_CONTENT",
            "message": "Subject or body cannot be empty"
        }

    try:
        # ---------- Create Message ----------
        msg = MIMEMultipart()
        msg["From"] = EMAIL
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # ---------- Connect SMTP ----------
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
            server.starttls()
        except Exception as e:
            return {
                "status": "error",
                "code": "SMTP_CONNECTION_FAILED",
                "message": f"SMTP connection failed: {str(e)}"
            }

        # ---------- Login ----------
        try:
            server.login(EMAIL, PASSWORD)
        except smtplib.SMTPAuthenticationError:
            return {
                "status": "error",
                "code": "AUTH_FAILED",
                "message": "Authentication failed. Check Gmail App Password."
            }

        # ---------- Send ----------
        try:
            server.send_message(msg)
        except Exception as e:
            return {
                "status": "error",
                "code": "SEND_FAILED",
                "message": f"Failed to send email: {str(e)}"
            }

        return {
            "status": "success",
            "message": "Email sent successfully 💌",
            "to": to,
            "subject": subject
        }

    except Exception as e:
        return {
            "status": "error",
            "code": "UNKNOWN_ERROR",
            "message": str(e)
        }

    finally:
        try:
            if server:
                server.quit()
        except:
            pass