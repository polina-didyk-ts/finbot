import config
from typing import List


def _quote_tab(sheet_tab: str) -> str:
    # Sheet names with spaces/dots/Cyrillic must be quoted; single quotes are doubled
    return "'" + sheet_tab.replace("'", "''") + "'"


def _next_empty_row(sheets_service, spreadsheet_id: str, tab: str) -> int:
    """Row number right after the last row that has any value in columns A:G."""
    resp = (
        sheets_service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"{tab}!A:G")
        .execute()
    )
    rows = resp.get("values", [])
    # the API trims trailing empty rows, but keep a guard for rows of empty strings
    last = len(rows)
    while last > 0 and not any(str(c).strip() for c in rows[last - 1]):
        last -= 1
    return last + 1


def append_expense_row(
    sheets_service,
    sheet_tab: str,
    date: str,
    amount: str,
    description: str,
    receipt_link: str,
    is_income: bool = False,
) -> None:
    spreadsheet_id = config.GOOGLE_SHEET_ID
    if not spreadsheet_id:
        raise RuntimeError("GOOGLE_SHEET_ID not configured")

    # Columns mapping:
    # A: date
    # B: empty (Знак 1)
    # C: empty (Знак 2)
    # D: description (Примечания)
    # E: amount if income (Приход)
    # F: amount if expense (Расход)
    # G: receipt_link (Чек)
    income = amount if is_income else ""
    expense = "" if is_income else amount
    values: List[List[str]] = [[date, "", "", description, income, expense, receipt_link]]

    # Write to an explicit A:G range of the next free row. values().append() guesses
    # where the "table" starts and, with manual edits in the sheet, sometimes shifted
    # the whole row several columns to the right.
    tab = _quote_tab(sheet_tab)
    row = _next_empty_row(sheets_service, spreadsheet_id, tab)
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{tab}!A{row}:G{row}",
        valueInputOption="USER_ENTERED",
        body={"values": values},
    ).execute()
