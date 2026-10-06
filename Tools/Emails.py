import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config_driver import Check_Keys

EMAIL = Check_Keys("KEYS", "EMAIL")
PASSWORD = Check_Keys("KEYS", "PASSWORD")


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

#Check new Mails
def check_new_mail(peek=True):
    mail = None
    try:
        cur_email = Check_Keys("KEYS", "EMAIL") or EMAIL
        cur_pass = Check_Keys("KEYS", "PASSWORD") or PASSWORD

        if not cur_email or not cur_pass:
            return None

        mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=10)
        mail.login(cur_email, cur_pass)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        if status != "OK" or not messages or not messages[0]:
            return None

        mail_ids = messages[0].split()
        if not mail_ids:
            return None

        latest_id = mail_ids[-1]
        fetch_mode = "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])" if peek else "(RFC822)"
        status, data = mail.fetch(latest_id, fetch_mode)
        if status != "OK" or not data or not data[0]:
            return None

        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        sender_raw = msg.get("from", "Unknown Sender")
        subject_raw = msg.get("subject", "No Subject")

        sender = decode_text(sender_raw)
        subject = decode_text(subject_raw)

        clean_sender = sender
        if "<" in sender and ">" in sender:
            name_part = sender.split("<")[0].strip().strip('"').strip("'")
            if name_part:
                clean_sender = name_part

        uid_str = latest_id.decode("utf-8", errors="ignore") if isinstance(latest_id, bytes) else str(latest_id)

        return {
            "type": "email",
            "id": uid_str,
            "sender": clean_sender,
            "full_sender": sender,
            "subject": subject,
            "message": f"New email received from {clean_sender}. Subject: {subject}"
        }
    except Exception:
        return None
    finally:
        if mail:
            try:
                mail.close()
            except Exception:
                pass
            try:
                mail.logout()
            except Exception:
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



def extract_body(msg):
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition"))

            # Plain text body
            if content_type == "text/plain" and "attachment" not in disposition:
                charset = part.get_content_charset() or "utf-8"
                body += part.get_payload(decode=True).decode(charset, errors="ignore")

            # HTML fallback (optional)
            elif content_type == "text/html" and not body:
                charset = part.get_content_charset() or "utf-8"
                body += part.get_payload(decode=True).decode(charset, errors="ignore")

    else:
        charset = msg.get_content_charset() or "utf-8"
        body = msg.get_payload(decode=True).decode(charset, errors="ignore")

    return body.strip()


def readmail_Full_body(index):
    mail = None
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        status, data = mail.search(None, "ALL")
        ids = data[0].split()

        if len(ids) < index:
            return {"status": "error", "message": "Invalid mail index"}

        selected_id = ids[-index]
        status, msg_data = mail.fetch(selected_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        subject = decode_text(msg.get("Subject"))
        sender = decode_text(msg.get("From"))
        body = extract_body(msg)   # ✅ same helper we created earlier

        return {
            "status": "success",
            "from": sender,
            "subject": subject,
            "body": body
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        if mail:
            mail.logout()
