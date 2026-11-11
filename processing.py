"""Messenger-independent receipt/income processing shared by the Telegram and Slack bots."""
import re
from datetime import datetime
from typing import Any, Dict, Tuple
from zoneinfo import ZoneInfo

import config
from currency import ISO_NUMERIC, format_amount, get_rate_to_uah, parse_amount
from google_clients import get_google_services
from google_drive import upload_receipt_to_drive
from google_sheets import append_expense_row
from ocr import extract_receipt_data

INCOME_PREFIX = "+"

# "+5000 опис", "+ 120,50 PLN опис", "+1 200.00 eur опис"
INCOME_TEXT_RE = re.compile(
    r"^\+\s*(\d[\d\s]*(?:[.,]\d{1,2})?)\s*([A-Za-z]{3}(?![A-Za-z]))?\s*(.*)$",
    re.DOTALL,
)

HELP_TEXT = (
    "📤 Витрата: надішли фото або файл чеку з описом у підписі, наприклад: ягоди в офіс\n\n"
    "📥 Надходження: почни повідомлення з «+»\n"
    "• фото/файл з підписом: + оплата від клієнта\n"
    "• або просто текст: +5000 оплата від клієнта (можна з валютою: +120 PLN повернення)"
)

NO_CAPTION_TEXT = (
    "Додайте опис у підписі до фото/файлу. Наприклад: ягоди в офіс\n"
    "Для надходження: + оплата від клієнта"
)


def today_str() -> str:
    return datetime.now(ZoneInfo(config.TIMEZONE)).strftime("%d.%m.%Y")


def is_income_text(text: str) -> bool:
    return (text or "").strip().startswith(INCOME_PREFIX)


def split_income(text: str) -> Tuple[bool, str]:
    text = (text or "").strip()
    if text.startswith(INCOME_PREFIX):
        return True, text[len(INCOME_PREFIX):].strip()
    return False, text


def convert_to_uah(amount: str, currency: str, description: str) -> Tuple[str, str, str]:
    """Return (sheet_amount, sheet_description, amount_display) with conversion to UAH."""
    currency = (currency or "UAH").upper()
    amount_value = parse_amount(amount)
    if amount_value is None:
        return amount, description, amount
    if currency == "UAH":
        formatted = format_amount(amount_value)
        return formatted, description, f"{formatted} UAH"

    original = f"{format_amount(amount_value)} {currency}"
    rate = get_rate_to_uah(currency)
    if rate:
        uah = format_amount(amount_value * rate)
        return (
            uah,
            f"{description} ({original}, курс {rate:.4f})",
            f"{uah} UAH ({original} × {rate:.4f}, курс Monobank)",
        )
    return (
        format_amount(amount_value),
        f"{description} ({original}, не конвертовано)",
        f"{original} ⚠️ курс не отримано, записано без конвертації",
    )


def process_file_entry(
    local_path: str,
    original_filename: str,
    caption_raw: str,
    user_cfg: Dict[str, Any],
) -> str:
    """OCR the file, upload it to Drive, append a row to Sheets. Returns the reply text."""
    is_income, caption = split_income(caption_raw)
    if not caption:
        return NO_CAPTION_TEXT

    receipt_data = extract_receipt_data(local_path)
    amount = receipt_data.get("amount", "")
    ocr_error = receipt_data.get("error", "")
    date_str = receipt_data.get("date", "") or today_str()

    drive_service, sheets_service = get_google_services()
    receipt_link = upload_receipt_to_drive(
        drive_service, local_path, original_filename, caption
    )

    sheet_amount, sheet_description, amount_str = convert_to_uah(
        amount, receipt_data.get("currency", ""), caption
    )

    append_expense_row(
        sheets_service,
        user_cfg["sheet_tab"],
        date_str,
        sheet_amount,
        sheet_description,
        receipt_link,
        is_income=is_income,
    )

    if not amount_str:
        amount_str = f"(не розпізнано: {ocr_error})" if ocr_error else "(не розпізнано)"

    title = "Надходження додано 📥" if is_income else "Чек додано ✅"
    return (
        f"{title}\n\n"
        f"Користувач: {user_cfg.get('name')}\n"
        f"Вкладка: {user_cfg.get('sheet_tab')}\n"
        f"Дата: {date_str}\n"
        f"Опис: {caption}\n"
        f"Сума: {amount_str}\n"
        f"Документ: {receipt_link}"
    )


def process_text_income(text: str, user_cfg: Dict[str, Any]) -> str:
    """Parse '+5000 опис' / '+120 PLN опис' and append an income row. Returns the reply text."""
    match = INCOME_TEXT_RE.match((text or "").strip())
    if not match:
        return (
            "Не зрозумів суму. Формат надходження: +5000 оплата від клієнта\n"
            "або з валютою: +120 PLN повернення"
        )

    amount = match.group(1).replace(" ", "")
    currency = (match.group(2) or "UAH").upper()
    description = match.group(3).strip()
    if currency != "UAH" and currency not in ISO_NUMERIC:
        # not a currency code, e.g. "+500 SEO послуги" — keep it in the description
        description = f"{match.group(2)} {description}".strip()
        currency = "UAH"
    if not description:
        return "Додайте опис після суми. Наприклад: +5000 оплата від клієнта"

    sheet_amount, sheet_description, amount_str = convert_to_uah(
        amount, currency, description
    )
    date_str = today_str()

    _, sheets_service = get_google_services()
    append_expense_row(
        sheets_service,
        user_cfg["sheet_tab"],
        date_str,
        sheet_amount,
        sheet_description,
        "",
        is_income=True,
    )

    return (
        "Надходження додано 📥\n\n"
        f"Користувач: {user_cfg.get('name')}\n"
        f"Вкладка: {user_cfg.get('sheet_tab')}\n"
        f"Дата: {date_str}\n"
        f"Опис: {description}\n"
        f"Сума: {amount_str}"
    )
