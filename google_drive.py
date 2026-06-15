import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import config


def get_current_month_folder_name() -> str:
    tz = ZoneInfo(config.TIMEZONE)
    now = datetime.now(tz)
    months = {
        1: "Січень",
        2: "Лютий",
        3: "Березень",
        4: "Квітень",
        5: "Травень",
        6: "Червень",
        7: "Липень",
        8: "Серпень",
        9: "Вересень",
        10: "Жовтень",
        11: "Листопад",
        12: "Грудень",
    }
    return months.get(now.month, now.strftime("%B"))


def get_or_create_month_folder(drive_service) -> str:
    root_id = config.GOOGLE_DRIVE_ROOT_FOLDER_ID
    if not root_id:
        raise RuntimeError("GOOGLE_DRIVE_ROOT_FOLDER_ID not configured")

    month_name = get_current_month_folder_name()
    query = (
        f"'{root_id}' in parents and name = '{month_name}'"
        " and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )

    try:
        resp = (
            drive_service.files()
            .list(q=query, spaces='drive', fields='files(id,name)',
                  supportsAllDrives=True, includeItemsFromAllDrives=True)
            .execute()
        )
        files = resp.get("files", [])
        if files:
            return files[0]["id"]

        # create folder
        file_metadata = {
            "name": month_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [root_id],
        }
        created = (
            drive_service.files()
            .create(body=file_metadata, fields='id', supportsAllDrives=True)
            .execute()
        )
        return created.get("id")
    except HttpError as e:
        raise


def make_safe_filename_part(text: str) -> str:
    if not text:
        return "no-description"
    safe = text.lower()
    safe = safe.replace(" ", "-")
    for ch in ["/", "\\"]:
        safe = safe.replace(ch, "-")
    # remove characters that are problematic
    safe = "".join(c for c in safe if c.isalnum() or c in "-_")
    return safe[:40]


def upload_receipt_to_drive(
    drive_service,
    local_file_path: str,
    original_filename: str,
    description: str,
) -> str:
    month_folder_id = get_or_create_month_folder(drive_service)

    tz = ZoneInfo(config.TIMEZONE)
    now = datetime.now(tz)
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    _, ext = os.path.splitext(original_filename or "")
    ext = ext or ""
    safe_desc = make_safe_filename_part(description)
    filename = f"{now.strftime('%Y-%m-%d')}_{now.strftime('%H-%M-%S')}_{safe_desc}{ext}"

    media = MediaFileUpload(local_file_path, resumable=True)
    file_metadata = {
        "name": filename,
        "parents": [month_folder_id],
        "description": description,
    }

    created = (
        drive_service.files()
        .create(body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True)
        .execute()
    )

    return created.get("webViewLink") or f"https://drive.google.com/file/d/{created.get('id')}/view"
