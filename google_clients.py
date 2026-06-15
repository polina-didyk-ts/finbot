import json
import os
from typing import Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config


def get_google_services() -> Tuple[object, object]:
    """Return (drive_service, sheets_service).

    Drive: always uses OAuth credentials (from env JSON, token file, or interactive flow).
    Sheets: uses Service Account if GOOGLE_SERVICE_ACCOUNT_JSON is present, otherwise uses the same OAuth credentials.
    """

    DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
    SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    # Prepare Sheets credentials: prefer Service Account JSON from env
    sa_json_env = config.GOOGLE_SERVICE_ACCOUNT_JSON
    sheets_creds = None
    if sa_json_env:
        try:
            sa_info = json.loads(sa_json_env)
            sheets_creds = service_account.Credentials.from_service_account_info(
                sa_info, scopes=SHEETS_SCOPES
            )
        except Exception as e:
            raise RuntimeError(f"Failed to parse GOOGLE_SERVICE_ACCOUNT_JSON: {e}")

    # Prepare Drive (OAuth) credentials
    drive_creds = None

    # 1) Try token JSON from env
    token_json_env = config.GOOGLE_TOKEN_JSON
    if token_json_env:
        try:
            info = json.loads(token_json_env)
            drive_creds = Credentials.from_authorized_user_info(info, DRIVE_SCOPES)
        except Exception as e:
            raise RuntimeError(f"Failed to parse GOOGLE_TOKEN_JSON: {e}")

    # 2) Try token file
    token_file = config.GOOGLE_OAUTH_TOKEN_FILE
    if not drive_creds and token_file and os.path.exists(token_file):
        try:
            drive_creds = Credentials.from_authorized_user_file(token_file, DRIVE_SCOPES)
        except Exception as e:
            raise RuntimeError(f"Failed to read token file {token_file}: {e}")

    # 3) If we don't have valid creds, do OAuth flow (using client secret from env or file)
    client_secret_json = config.GOOGLE_CLIENT_SECRET_JSON
    client_secret_file = config.GOOGLE_OAUTH_CLIENT_SECRET_FILE

    if not drive_creds or not drive_creds.valid:
        if drive_creds and drive_creds.expired and drive_creds.refresh_token:
            try:
                drive_creds.refresh(Request())
            except Exception:
                drive_creds = None

        if not drive_creds or not drive_creds.valid:
            # Need to run interactive flow
            if client_secret_json:
                try:
                    client_config = json.loads(client_secret_json)
                    flow = InstalledAppFlow.from_client_config(client_config, DRIVE_SCOPES)
                    drive_creds = flow.run_local_server(port=0)
                except Exception as e:
                    raise RuntimeError(f"Failed to use GOOGLE_CLIENT_SECRET_JSON for OAuth flow: {e}")
            elif client_secret_file and os.path.exists(client_secret_file):
                flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, DRIVE_SCOPES)
                drive_creds = flow.run_local_server(port=0)
            else:
                raise RuntimeError("No OAuth client secret available (set GOOGLE_CLIENT_SECRET_JSON or GOOGLE_OAUTH_CLIENT_SECRET_FILE)")

            # persist token back to token file if configured
            if token_file:
                try:
                    with open(token_file, "w") as f:
                        f.write(drive_creds.to_json())
                except Exception:
                    pass

    # Build services
    drive_service = build("drive", "v3", credentials=drive_creds)

    # Sheets: prefer service account creds, otherwise use drive (OAuth) creds
    if sheets_creds:
        sheets_service = build("sheets", "v4", credentials=sheets_creds)
    else:
        sheets_service = build("sheets", "v4", credentials=drive_creds)

    return drive_service, sheets_service
