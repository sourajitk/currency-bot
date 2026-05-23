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
}

PATTERN = re.compile(
    r"(?i)(?:(?<!\w)(\d(?:[\d.,]*\d)?)\s*(k|m|b|t|l|cr)?\s*([A-Za-z]{3}|[\$€£₹¥₽₩₪])(?!\w))|"
    r"(?:(?<!\w)([A-Za-z]{3}|[\$€£₹¥₽₩₪])\s*(\d(?:[\d.,]*\d)?)\s*(k|m|b|t|l|cr)?(?!\w))"
)


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
