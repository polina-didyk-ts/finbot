import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import config


def get_google_services():
    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
    ]

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
