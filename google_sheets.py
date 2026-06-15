import config
from typing import Optional, List


def append_expense_row(
    sheets_service,
    sheet_tab: str,
    date: str,
    amount: str,
    description: str,
    receipt_link: str,
) -> None:
    spreadsheet_id = config.GOOGLE_SHEET_ID
    if not spreadsheet_id:
        raise RuntimeError("GOOGLE_SHEET_ID not configured")

    range_name = f"{sheet_tab}!A:G"

    # Columns mapping:
    # A: date
    # B: empty (Знак 1)
    # C: empty (Знак 2)
    # D: description (Примечания)
    # E: empty (Приход)
    # F: amount (Расход)
    # G: receipt_link (Чек)
    values: List[List[str]] = [[date, "", "", description, "", amount, receipt_link]]

    body = {"values": values}
    sheets_service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()
