"""Telegram bot entry point. Business logic lives in processing.py (shared with slack_bot.py)."""
import os
import tempfile
import traceback
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
from processing import (
    HELP_TEXT,
    NO_CAPTION_TEXT,
    process_file_entry,
    process_text_income,
    split_income,
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Привіт!\n\n{HELP_TEXT}")


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

        caption_raw = update.message.caption or ""
        if not split_income(caption_raw)[1]:
            await update.message.reply_text(NO_CAPTION_TEXT)
            return

        if update.message.photo:
            file_obj = await update.message.photo[-1].get_file()
            original_filename = "receipt.jpg"
        elif update.message.document:
            file_obj = await update.message.document.get_file()
            original_filename = update.message.document.file_name or "receipt"
        else:
            await update.message.reply_text("Надішліть фото або файл чеку.")
            return

        with tempfile.TemporaryDirectory() as td:
            local_path = os.path.join(td, original_filename)
            await file_obj.download_to_drive(custom_path=local_path)
            reply = process_file_entry(local_path, original_filename, caption_raw, user_cfg)

        await update.message.reply_text(reply)

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
        await update.message.reply_text(
            process_text_income(update.message.text or "", user_cfg)
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
