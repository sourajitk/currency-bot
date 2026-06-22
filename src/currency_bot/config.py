import re
import json
import os
import logging

logger = logging.getLogger(__name__)

DEFAULT_TARGETS = ["USD", "AED", "EUR"]
FALLBACK_TARGET = None
PREFS_FILE = "preferences.json"

SYMBOL_MAP = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "₹": "INR",
    "¥": "JPY",
    "₽": "RUB",
    "₩": "KRW",
    "₪": "ILS",
    "₺": "TRY",
    "₱": "PHP",
    "đ": "VND",
    "Đ": "VND",
}

# Currencies that use European-style formatting (comma as decimal separator, period as thousands separator)
EUROPEAN_STYLE_CURRENCIES = {"EUR", "BRL", "TRY", "VND", "IDR", "ALL"}

# Main regex pattern used to detect currency mentions. It matches two primary forms:
# 1. Amount first: e.g., "100.50 k USD"
# 2. Symbol first: e.g., "$ 100.50 k"
# It looks for word boundaries `(?<!\w)` and `(?!\w)` to avoid matching partial words.
PATTERN = re.compile(
    r"(?i)(?:(?<!\w)(\d(?:[\d.,]*\d)?)\s*(k|m|b|t|l|cr)?\s*([A-Za-z]{3}|[\$€£₹¥₽₩₪₺₱đ])(?!\w))|"
    r"(?:(?<!\w)([A-Za-z]{3}|[\$€£₹¥₽₩₪₺₱đ])\s*(\d(?:[\d.,]*\d)?)\s*(k|m|b|t|l|cr)?(?!\w))"
)

# Common 3-letter English words that are also currency codes.
# These will be ignored if matched in lowercase or mixed case to avoid false positives.
AMBIGUOUS_CURRENCIES = {
    "TRY", "ALL", "PEN", "BOB", "COP", "CUP", "GEL", "KID", "MAD", "MOP", "RUB", "SOS", "TOP"
}


def load_preferences():
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, "r") as f:
                data = json.load(f)
                prefs = {}
                for k, v in data.items():
                    if isinstance(v, list):
                        prefs[int(k)] = {"targets": v, "format": "international"}
                    elif isinstance(v, dict):
                        prefs[int(k)] = v
                return prefs
        except Exception as e:
            logger.error(f"Error loading preferences: {e}")
    return {}


def save_preferences(prefs):
    try:
        with open(PREFS_FILE, "w") as f:
            json.dump(prefs, f)
    except Exception as e:
        logger.error(f"Error saving preferences: {e}")


USER_PREFERENCES = load_preferences()
SUPPORTED_CURRENCIES = set()
