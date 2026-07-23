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
    # Currency words and synonyms (matched case-insensitively)
    "dollar": "USD",
    "dollars": "USD",
    "buck": "USD",
    "bucks": "USD",
    "euro": "EUR",
    "euros": "EUR",
    "pound": "GBP",
    "pounds": "GBP",
    "quid": "GBP",
    "sterling": "GBP",
    "rupee": "INR",
    "rupees": "INR",
    "rs": "INR",
    "rs.": "INR",
    "yen": "JPY",
    "ruble": "RUB",
    "rubles": "RUB",
    "rouble": "RUB",
    "roubles": "RUB",
    "won": "KRW",
    "wons": "KRW",
    "shekel": "ILS",
    "shekels": "ILS",
    "lira": "TRY",
    "liras": "TRY",
    "peso": "PHP",
    "pesos": "PHP",
    "dong": "VND",
    "dongs": "VND",
    "dirham": "AED",
    "dirhams": "AED",
    "franc": "CHF",
    "francs": "CHF",
    "yuan": "CNY",
    "rmb": "CNY",
    "real": "BRL",
    "reais": "BRL",
    "reales": "BRL",
}

MULTIPLIER_MAP = {
    "k": 1_000,
    "th": 1_000,
    "thousand": 1_000,
    "thousands": 1_000,
    "grand": 1_000,
    "l": 100_000,
    "lac": 100_000,
    "lacs": 100_000,
    "lakh": 100_000,
    "lakhs": 100_000,
    "m": 1_000_000,
    "mn": 1_000_000,
    "mil": 1_000_000,
    "million": 1_000_000,
    "millions": 1_000_000,
    "cr": 10_000_000,
    "crore": 10_000_000,
    "crores": 10_000_000,
    "b": 1_000_000_000,
    "bn": 1_000_000_000,
    "bil": 1_000_000_000,
    "billion": 1_000_000_000,
    "billions": 1_000_000_000,
    "t": 1_000_000_000_000,
    "tn": 1_000_000_000_000,
    "tril": 1_000_000_000_000,
    "trillion": 1_000_000_000_000,
    "trillions": 1_000_000_000_000,
    "q": 1_000_000_000_000_000,
    "quad": 1_000_000_000_000_000,
    "quadrillion": 1_000_000_000_000_000,
    "quadrillions": 1_000_000_000_000_000,
}

# Currencies that use European-style formatting (comma as decimal separator, period as thousands separator)
EUROPEAN_STYLE_CURRENCIES = {"EUR", "BRL", "TRY", "VND", "IDR", "ALL"}

# Common 3-letter English words that are also currency codes.
# These will be ignored if matched in lowercase or mixed case to avoid false positives.
AMBIGUOUS_CURRENCIES = {
    "TRY", "ALL", "PEN", "BOB", "COP", "CUP", "GEL", "KID", "MAD", "MOP", "RUB", "SOS", "TOP"
}

# Standard 3-letter ISO 4217 currency codes to avoid treating random 3-letter words (e.g. "him", "for") as currencies
KNOWN_CURRENCIES = {
    "USD", "EUR", "GBP", "INR", "JPY", "CAD", "AUD", "CHF", "CNY", "BRL",
    "RUB", "KRW", "ILS", "TRY", "PHP", "VND", "AED", "SAR", "SGD", "HKD",
    "TWD", "PKR", "BDT", "NGN", "EGP", "ZAR", "MXN", "SEK", "NOK", "DKK",
    "PLN", "THB", "MYR", "IDR", "HUF", "CZK", "CLP", "KES", "UGX", "TZS",
    "GHS", "MAD", "XAF", "XOF", "XPF", "BHD", "KWD", "OMR", "QAR", "JOD",
    "LBP", "IQD", "ARS", "COP", "PEN", "CLP", "NZD", "DOP", "CRC", "UYU",
    "BOB", "PYG", "RSD", "BGN", "ALL", "GEL", "AMD", "AZN", "KZT", "UZS",
}

# Regex sub-patterns
_CURRENCY_WORDS_PAT = (
    r"[\$€£₹¥₽₩₪₺₱đĐ]|rs\.?|dollars?|bucks?|euros?|pounds?|quid|sterling|rupees?|"
    r"yen|rubles?|roubles?|wons?|shekels?|liras?|pesos?|dongs?|dirhams?|francs?|"
    r"yuans?|rmb|reais|reales|real"
)

_KNOWN_CODES_PAT = "|".join(sorted(KNOWN_CURRENCIES))

# Prefix currency can be: symbol/currency word, or a recognized 3-letter currency code
_PREFIX_CURRENCY_TOKEN_PAT = f"(?:{_CURRENCY_WORDS_PAT}|{_KNOWN_CODES_PAT})"

# Suffix currency can be: symbol/currency word, or any 3-letter currency code
_SUFFIX_CURRENCY_TOKEN_PAT = f"(?:{_CURRENCY_WORDS_PAT}|[A-Za-z]{{3}})"

_MULTIPLIER_TOKEN_PAT = (
    r"(?:quadrillion|quadrillions|trillion|trillions|billion|billions|"
    r"million|millions|thousand|thousands|crore|crores|lakh|lakhs|"
    r"grand|quad|tril|bil|mil|lac|lacs|cr|tn|bn|mn|th|k|m|b|t|l)"
)

# Main regex pattern used to detect currency mentions.
# Matches two primary forms:
# 1. Amount first: e.g. "1.65 trillion USD", "100.50 k EUR", "500 dollars"
# 2. Currency first: e.g. "$1.65 trillion", "USD 1.65 trillion", "rs. 500"
PATTERN = re.compile(
    r"(?i)(?:(?<!\w)(\d(?:[\d.,]*\d)?)\s*(" + _MULTIPLIER_TOKEN_PAT + r")?\s*(" + _SUFFIX_CURRENCY_TOKEN_PAT + r")(?!\w))|"
    r"(?:(?<!\w)(" + _PREFIX_CURRENCY_TOKEN_PAT + r")\s*(\d(?:[\d.,]*\d)?)\s*(" + _MULTIPLIER_TOKEN_PAT + r")?(?!\w))"
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
