import os
import re
import tempfile
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Tuple

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import config
from users import get_user_config
from google_clients import get_google_services
from google_drive import upload_receipt_to_drive
from google_sheets import append_expense_row
from ocr import extract_receipt_data
from currency import ISO_NUMERIC, get_rate_to_uah, parse_amount, format_amount


INCOME_PREFIX = "+"

# "+5000 опис", "+ 120,50 PLN опис", "+1 200.00 eur опис"
INCOME_TEXT_RE = re.compile(
    r"^\+\s*(\d[\d\s]*(?:[.,]\d{1,2})?)\s*([A-Za-z]{3}(?![A-Za-z]))?\s*(.*)$",
    re.DOTALL,
)


def _today_str() -> str:
    return datetime.now(ZoneInfo(config.TIMEZONE)).strftime("%d.%m.%Y")


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


def _split_income(text: str) -> Tuple[bool, str]:
    text = text.strip()
    if text.startswith(INCOME_PREFIX):
        return True, text[len(INCOME_PREFIX):].strip()
    return False, text


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привіт!\n\n"
        "📤 Витрата: надішли фото або файл чеку з описом у підписі, наприклад: ягоди в офіс\n\n"
        "📥 Надходження: почни повідомлення з «+»\n"
        "• фото/файл з підписом: + оплата від клієнта\n"
        "• або просто текст: +5000 оплата від клієнта (можна з валютою: +120 PLN повернення)"
    )


async def whoami_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f"user_id: {user.id}\nusername: {user.username}")


async def _get_allowed_user(update: Update) -> Optional[dict]:
    user_cfg = get_user_config(update.effective_user.id)
    if not user_cfg:
        await update.message.reply_text(
            "У вас поки немає доступу до цього бота. Надішліть адміну ваш /whoami."
        )
    return user_cfg


async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_cfg = await _get_allowed_user(update)
        if not user_cfg:
            return

        is_income, caption = _split_income(update.message.caption or "")
        if not caption:
            await update.message.reply_text(
                "Додайте опис у підписі до фото/файлу. Наприклад: ягоди в офіс\n"
                "Для надходження: + оплата від клієнта"
            )
            return

        # determine file
        file_obj = None
        original_filename = "receipt"
        if update.message.photo:
            file_obj = await update.message.photo[-1].get_file()
            original_filename = "receipt.jpg"
        elif update.message.document:
            file_obj = await update.message.document.get_file()
            original_filename = update.message.document.file_name or "receipt"
        else:
            await update.message.reply_text("Надішліть фото або файл чеку.")
            return

        # download to temp
        with tempfile.TemporaryDirectory() as td:
            local_path = os.path.join(td, original_filename)
            await file_obj.download_to_drive(custom_path=local_path)
            receipt_data = extract_receipt_data(local_path)
            amount = receipt_data.get("amount", "")
            ocr_date = receipt_data.get("date", "")
            ocr_error = receipt_data.get("error", "")

            drive_service, sheets_service = get_google_services()
            receipt_link = upload_receipt_to_drive(
                drive_service, local_path, original_filename, caption
            )

        date_str = ocr_date or _today_str()

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
        await update.message.reply_text(
            f"{title}\n\n"
            f"Користувач: {user_cfg.get('name')}\n"
            f"Вкладка: {user_cfg.get('sheet_tab')}\n"
            f"Дата: {date_str}\n"
            f"Опис: {caption}\n"
            f"Сума: {amount_str}\n"
            f"Документ: {receipt_link}"
        )

    except Exception:
        traceback.print_exc()
        await update.message.reply_text(
            "Сталася помилка під час обробки чеку. Перевірте лог сервера."
        )


async def handle_text_income(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_cfg = await _get_allowed_user(update)
        if not user_cfg:
            return

        match = INCOME_TEXT_RE.match((update.message.text or "").strip())
        if not match:
            await update.message.reply_text(
                "Не зрозумів суму. Формат надходження: +5000 оплата від клієнта\n"
                "або з валютою: +120 PLN повернення"
            )
            return

        amount = match.group(1).replace(" ", "")
        currency = (match.group(2) or "UAH").upper()
        description = match.group(3).strip()
        if currency != "UAH" and currency not in ISO_NUMERIC:
            # not a currency code, e.g. "+500 SEO послуги" — keep it in the description
            description = f"{match.group(2)} {description}".strip()
            currency = "UAH"
        if not description:
            await update.message.reply_text(
                "Додайте опис після суми. Наприклад: +5000 оплата від клієнта"
            )
            return

        sheet_amount, sheet_description, amount_str = convert_to_uah(
            amount, currency, description
        )
        date_str = _today_str()

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

        await update.message.reply_text(
            "Надходження додано 📥\n\n"
            f"Користувач: {user_cfg.get('name')}\n"
            f"Вкладка: {user_cfg.get('sheet_tab')}\n"
            f"Дата: {date_str}\n"
            f"Опис: {description}\n"
            f"Сума: {amount_str}"
        )

    except Exception:
        traceback.print_exc()
        await update.message.reply_text(
            "Сталася помилка під час запису надходження. Перевірте лог сервера."
        )


def main() -> None:
    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not configured in environment")

    app = (
        ApplicationBuilder()
        .token(token)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("whoami", whoami_command))
    app.add_handler(
        MessageHandler(filters.PHOTO | filters.Document.ALL, handle_receipt)
    )
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Regex(r"^\s*\+"),
            handle_text_income,
        )
    )

    print("Bot started (polling)")
    app.run_polling()


if __name__ == "__main__":
    main()
