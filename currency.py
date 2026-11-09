import json
import logging
import ssl
import time
import urllib.request
from typing import Optional

import certifi

# python.org builds on macOS don't use system certificates — use certifi's bundle
_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

MONOBANK_URL = "https://api.monobank.ua/bank/currency"
UAH_CODE = 980
CACHE_TTL_SECONDS = 300  # Monobank public API allows ~1 request per 5 minutes

# ISO 4217 alpha -> numeric codes for currencies we expect on receipts
ISO_NUMERIC = {
    "PLN": 985,
    "USD": 840,
    "EUR": 978,
    "CZK": 203,
    "GBP": 826,
    "HUF": 348,
    "CHF": 756,
    "RON": 946,
}

_cache: dict = {"rates": None, "fetched_at": 0.0}


def _fetch_rates() -> Optional[list]:
    now = time.time()
    if _cache["rates"] is not None and now - _cache["fetched_at"] < CACHE_TTL_SECONDS:
        return _cache["rates"]
    try:
        req = urllib.request.Request(MONOBANK_URL, headers={"User-Agent": "finance-receipt-bot"})
        with urllib.request.urlopen(req, timeout=10, context=_SSL_CONTEXT) as resp:
            rates = json.loads(resp.read().decode("utf-8"))
        _cache["rates"] = rates
        _cache["fetched_at"] = now
        return rates
    except Exception:
        # On rate limit (429) or network error, fall back to the last known rates
        logging.exception("Currency: failed to fetch Monobank rates")
        return _cache["rates"]


def get_rate_to_uah(currency: str) -> Optional[float]:
    """Rate Monobank uses for card payments in `currency` (UAH per 1 unit)."""
    code = ISO_NUMERIC.get(currency.upper())
    if code is None:
        return None
    rates = _fetch_rates()
    if not rates:
        return None
    for r in rates:
        if r.get("currencyCodeA") == code and r.get("currencyCodeB") == UAH_CODE:
            # Card payments are charged at the sell rate; minor currencies only have a cross rate
            return r.get("rateSell") or r.get("rateCross")
    return None


def parse_amount(amount: str) -> Optional[float]:
    if not amount:
        return None
    try:
        return float(amount.replace(" ", "").replace(",", "."))
    except ValueError:
        return None


def format_amount(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")
