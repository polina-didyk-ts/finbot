import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import config


def get_google_services():
    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    # Check if Service Account JSON is provided via env
    sa_json_env = config.GOOGLE_SERVICE_ACCOUNT_JSON
    if sa_json_env:
        try:
            sa_info = json.loads(sa_json_env)
            creds = service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)
            drive_service = build("drive", "v3", credentials=creds)
            sheets_service = build("sheets", "v4", credentials=creds)
            return drive_service, sheets_service
        except Exception as e:
            raise RuntimeError(f"Failed to parse GOOGLE_SERVICE_ACCOUNT_JSON: {e}")

    # Fallback to OAuth flow
    client_secret_file = config.GOOGLE_OAUTH_CLIENT_SECRET_FILE
    token_file = config.GOOGLE_OAUTH_TOKEN_FILE

    if not client_secret_file:
        raise RuntimeError("GOOGLE_OAUTH_CLIENT_SECRET_FILE is not set in environment")

    creds = None
    if token_file and os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            creds = flow.run_local_server(port=0)

        if token_file:
            with open(token_file, "w") as token:
                token.write(creds.to_json())

    drive_service = build("drive", "v3", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)

    return drive_service, sheets_service
