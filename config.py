from dotenv import load_dotenv
import os
from typing import Optional

load_dotenv()

TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_OAUTH_CLIENT_SECRET_FILE: Optional[str] = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_FILE")
GOOGLE_OAUTH_TOKEN_FILE: Optional[str] = os.getenv("GOOGLE_OAUTH_TOKEN_FILE")
GOOGLE_SERVICE_ACCOUNT_FILE: Optional[str] = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
GOOGLE_SERVICE_ACCOUNT_JSON: Optional[str] = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_DRIVE_ROOT_FOLDER_ID: Optional[str] = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID")
GOOGLE_SHEET_ID: Optional[str] = os.getenv("GOOGLE_SHEET_ID")
ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
TIMEZONE: str = os.getenv("TIMEZONE", "Europe/Warsaw")
