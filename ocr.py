import base64
import json
import logging
import os
from typing import Any

import anthropic
import config


def _get_media_type(image_path: str) -> str:
    _, ext = os.path.splitext(image_path.lower())
    if ext in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".pdf":
        return "application/pdf"
    return "application/octet-stream"


def _clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[len("```json"): -3].strip()
    elif text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()
    return text


def extract_receipt_data(image_path: str) -> dict[str, str]:
    if not image_path or not os.path.exists(image_path):
        logging.error("OCR: image_path is missing or does not exist: %s", image_path)
        return {"amount": "", "date": ""}

    api_key = config.ANTHROPIC_API_KEY
    if not api_key:
        logging.error("OCR: ANTHROPIC_API_KEY is not configured")
        return {"amount": "", "date": ""}

    media_type = _get_media_type(image_path)
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")

        prompt = (
            "Це фото або скан фінансового документу: товарний чек, квитанція "
            "про оплату, банківська квитанція або інвойс. "
            "Витягни два значення:\n"
            "1. Суму операції/платежу/покупки (не комісію, не код авторизації, "
            "не номер картки чи рахунку). Якщо банківська квитанція — бери поле "
            "'Сума' транзакції, ігноруючи комісію.\n"
            "2. Дату операції у форматі ДД.ММ.РРРР (дата самої покупки/платежу, "
            "а не дата друку чи інша).\n\n"
            "Відповідай ТІЛЬКИ у форматі JSON без жодного додаткового тексту:\n"
            '{"amount": "320.50", "date": "15.06.2026"}\n\n'
            "Якщо суму або дату визначити неможливо — залиш відповідне поле "
            "порожнім рядком."
        )

        client = anthropic.Anthropic(api_key=api_key)

        if media_type == "application/pdf":
            content_block = {
                "type": "document",
                "source": {
                    "type": "base64",
                    "data": encoded,
                    "media_type": media_type,
                },
            }
        else:
            content_block = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": encoded,
                },
            }

        response = client.messages.create(
            model="claude-sonnet-4-5",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        content_block,
                    ],
                }
            ],
            max_tokens=100,
        )

        if not response or not hasattr(response, "content"):
            logging.error("OCR: unexpected Anthropic response format")
            return {"amount": "", "date": ""}

        first_content = response.content[0]
        raw_text = getattr(first_content, "text", "") or ""
        cleaned_text = _clean_json_text(raw_text)

        parsed = json.loads(cleaned_text)
        amount = str(parsed.get("amount", ""))
        date = str(parsed.get("date", ""))
        return {"amount": amount.replace(".", ","), "date": date}
    except Exception:
        logging.exception("OCR: failed to extract receipt data from image %s", image_path)
        return {"amount": "", "date": ""}
