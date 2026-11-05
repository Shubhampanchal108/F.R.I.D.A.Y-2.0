import os
import json
import logging
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from utils.paths import DOCS_PATH
from config.config_driver import load_data

logger = logging.getLogger("Friday.Calendar.Auth")

# Full calendar access scope to support all features
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events"
]

CALENDAR_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(CALENDAR_DIR, "token.json")
LOCAL_CREDENTIALS_PATH = os.path.join(CALENDAR_DIR, "credentials.json")
GLOBAL_TOKEN_PATH = os.path.join(DOCS_PATH, "calendar_token.json")


def get_token_path() -> str:
    """Returns preferred path for storing token.json."""
    if os.path.exists(TOKEN_PATH):
        return TOKEN_PATH
    if os.path.exists(GLOBAL_TOKEN_PATH):
        return GLOBAL_TOKEN_PATH
    return TOKEN_PATH


def get_client_config() -> Optional[dict]:
    """
    Retrieves Google OAuth client configuration either from:
    1. UI / config.json (KEYS.GOOGLE_CALENDAR_CLIENT_ID and GOOGLE_CALENDAR_CLIENT_SECRET)
    2. Local credentials.json file in integrations/calender/credentials.json
    """
    # 1. Check UI / config.json via load_data (non-blocking)
    try:
        data = load_data()
        keys = data.get("KEYS", {})
        client_id = keys.get("GOOGLE_CALENDAR_CLIENT_ID", "")
        client_secret = keys.get("GOOGLE_CALENDAR_CLIENT_SECRET", "")

        if client_id and client_secret and client_id.strip() and client_secret.strip():
            return {
                "installed": {
                    "client_id": client_id.strip(),
                    "client_secret": client_secret.strip(),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["http://localhost", "http://localhost:8080/"]
                }
            }
    except Exception as e:
        logger.warning(f"Error loading client config from config.json: {e}")

    # 2. Check credentials.json file
    if os.path.exists(LOCAL_CREDENTIALS_PATH):
        try:
            with open(LOCAL_CREDENTIALS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read local credentials.json: {e}")

    return None


def get_credentials(interactive: bool = True) -> Optional[Credentials]:
    """
    Loads, refreshes, or initiates OAuth authorization for Google Calendar.
    Returns valid Credentials instance or None if not configured.
    """
    creds = None
    token_file = get_token_path()

    # 1. Load saved token if present
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        except Exception as e:
            logger.warning(f"Failed to load cached calendar token: {e}")
            creds = None

    # 2. Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_file, "w", encoding="utf-8") as token_out:
                    token_out.write(creds.to_json())
                return creds
            except Exception as e:
                logger.warning(f"Failed to refresh expired calendar token: {e}")
                creds = None

        if not interactive:
            return None

        # 3. New authorization flow
        client_config = get_client_config()
        if not client_config:
            logger.info("Google Calendar client credentials not configured.")
            return None

        try:
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
            
            # Save token for next sessions
            os.makedirs(os.path.dirname(token_file), exist_ok=True)
            with open(token_file, "w", encoding="utf-8") as token_out:
                token_out.write(creds.to_json())
        except Exception as e:
            logger.error(f"Google Calendar OAuth flow error: {e}")
            return None

    return creds
