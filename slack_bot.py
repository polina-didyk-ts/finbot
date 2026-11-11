"""Slack bot entry point (Socket Mode). Business logic lives in processing.py (shared with app.py).

Users post receipts to a shared channel; the bot replies in the message thread.
Run: python slack_bot.py
"""
import html
import logging
import os
import re
import ssl
import tempfile
import traceback
import urllib.request

import certifi
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

import config
from processing import (
    HELP_TEXT,
    is_income_text,
    process_file_entry,
    process_text_income,
)
from users import get_slack_user_config

logging.basicConfig(level=logging.INFO)

# python.org builds on macOS don't use system certificates — use certifi's bundle
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

# Slack bot works with its own (2027) spreadsheet and Drive folder when configured
if config.SLACK_GOOGLE_SHEET_ID:
    config.GOOGLE_SHEET_ID = config.SLACK_GOOGLE_SHEET_ID
if config.SLACK_GOOGLE_DRIVE_ROOT_FOLDER_ID:
    config.GOOGLE_DRIVE_ROOT_FOLDER_ID = config.SLACK_GOOGLE_DRIVE_ROOT_FOLDER_ID

if not config.SLACK_BOT_TOKEN or not config.SLACK_APP_TOKEN:
    raise RuntimeError("SLACK_BOT_TOKEN and SLACK_APP_TOKEN must be configured")

web_client = WebClient(token=config.SLACK_BOT_TOKEN, ssl=SSL_CONTEXT)
app = App(client=web_client)

# Messages without a file that the bot should not react to (regular chat in the channel)
HELP_RE = re.compile(r"^\s*(help|допомога|\?)\s*$", re.IGNORECASE)


def _clean_text(text: str) -> str:
    # Slack escapes &, <, > in message text
    return html.unescape(text or "").strip()


def _download_slack_file(file_info: dict, dest_dir: str) -> str:
    url = file_info.get("url_private_download") or file_info.get("url_private")
    if not url:
        raise RuntimeError(f"Slack file {file_info.get('id')} has no download URL")
    filename = os.path.basename(file_info.get("name") or "receipt")
    local_path = os.path.join(dest_dir, filename)
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {config.SLACK_BOT_TOKEN}"}
    )
    with urllib.request.urlopen(req, timeout=60, context=SSL_CONTEXT) as resp, open(
        local_path, "wb"
    ) as f:
        f.write(resp.read())
    return local_path


@app.event("message")
def handle_message(event, say, logger):
    # only plain user messages and file uploads; skip edits, joins, bot messages
    if event.get("subtype") not in (None, "file_share") or event.get("bot_id"):
        return
    # only top-level messages; replies inside threads are regular conversation
    if event.get("thread_ts") and event.get("thread_ts") != event.get("ts"):
        return
    if config.SLACK_CHANNEL_ID and event.get("channel") != config.SLACK_CHANNEL_ID:
        return

    text = _clean_text(event.get("text", ""))
    files = event.get("files") or []
    thread_ts = event["ts"]

    if not files:
        if HELP_RE.match(text):
            say(text=HELP_TEXT, thread_ts=thread_ts)
            return
        if not is_income_text(text):
            return  # ordinary chat message, ignore

    user_id = event.get("user")
    user_cfg = get_slack_user_config(user_id)
    if not user_cfg:
        say(
            text=(
                "У вас поки немає доступу до цього бота.\n"
                f"Ваш Slack ID: `{user_id}` — надішліть його адміну."
            ),
            thread_ts=thread_ts,
        )
        return

    try:
        if not files:
            say(text=process_text_income(text, user_cfg), thread_ts=thread_ts)
            return

        # each attached file is a separate receipt with the same description
        for file_info in files:
            with tempfile.TemporaryDirectory() as td:
                local_path = _download_slack_file(file_info, td)
                reply = process_file_entry(
                    local_path, os.path.basename(local_path), text, user_cfg
                )
            say(text=reply, thread_ts=thread_ts)
    except Exception:
        traceback.print_exc()
        say(
            text="Сталася помилка під час обробки. Перевірте лог сервера.",
            thread_ts=thread_ts,
        )


def main() -> None:
    print("Slack bot started (Socket Mode)")
    SocketModeHandler(app, config.SLACK_APP_TOKEN, web_client=web_client).start()


if __name__ == "__main__":
    main()
