import base64
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


def extract_amount(image_path: str) -> str:
    if not image_path or not os.path.exists(image_path):
        logging.error("OCR: image_path is missing or does not exist: %s", image_path)
        return ""

    api_key = config.ANTHROPIC_API_KEY
    if not api_key:
        logging.error("OCR: ANTHROPIC_API_KEY is not configured")
        return ""

    media_type = _get_media_type(image_path)
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")

        prompt = (
            "Витягни лише фінальну суму до сплати з чеку. "
            "Відповідай тільки числом без валюти і пробілів, наприклад: 320.50. "
            "Якщо суму визначити неможливо — повертай порожній рядок."
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
            return ""

        first_content = response.content[0]
        result = getattr(first_content, "text", "") or ""
        return result.replace(".", ",")
    except Exception:
        logging.exception("OCR: failed to extract amount from image %s", image_path)
        return ""
