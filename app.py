import os
import tempfile
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

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


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привіт! Надішли фото або файл чеку з описом у підписі, наприклад: ягоди в офіс"
    )


async def whoami_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f"user_id: {user.id}\nusername: {user.username}")


async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = update.effective_user
        user_cfg = get_user_config(user.id)
        if not user_cfg:
            await update.message.reply_text(
                "У вас поки немає доступу до цього бота. Надішліть адміну ваш /whoami."
            )
            return

        caption = (update.message.caption or "").strip()
        if not caption:
            await update.message.reply_text(
                "Додайте опис у підписі до фото/файлу. Наприклад: ягоди в офіс"
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

            drive_service, sheets_service = get_google_services()
            receipt_link = upload_receipt_to_drive(
                drive_service, local_path, original_filename, caption
            )

        tz = ZoneInfo(config.TIMEZONE)
        date_str = datetime.now(tz).strftime("%d.%m.%Y")

        append_expense_row(
            sheets_service,
            user_cfg["sheet_tab"],
            date_str,
            amount,
            caption,
            receipt_link,
        )

        await update.message.reply_text(
            "Чек додано ✅\n\n"
            f"Користувач: {user_cfg.get('name')}\n"
            f"Вкладка: {user_cfg.get('sheet_tab')}\n"
            f"Дата: {date_str}\n"
            f"Опис: {caption}\n"
            f"Сума: {amount if amount else '(не розпізнано)'}\n"
            f"OCR-дата: {ocr_date if ocr_date else '(не розпізнано)'}\n"
            f"Чек: {receipt_link}"
        )

    except Exception as e:
        traceback.print_exc()
        await update.message.reply_text(
            "Сталася помилка під час обробки чеку. Перевірте лог сервера."
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

    print("Bot started (polling)")
    app.run_polling()


if __name__ == "__main__":
    main()
