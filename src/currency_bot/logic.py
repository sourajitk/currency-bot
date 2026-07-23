from .config import (
    PATTERN,
    SYMBOL_MAP,
    MULTIPLIER_MAP,
    SUPPORTED_CURRENCIES,
    KNOWN_CURRENCIES,
    USER_PREFERENCES,
    DEFAULT_TARGETS,
    FALLBACK_TARGET,
    AMBIGUOUS_CURRENCIES,
    EUROPEAN_STYLE_CURRENCIES,
)


def parse_amount(amount_str, currency=None):
    """
    Intelligently parses an amount string into a float, taking into account both
    US/UK and European number formats.
    """
    if "." in amount_str and "," in amount_str:
        # Both separators exist: determine which is the decimal by looking at the last one
        if amount_str.rfind(",") > amount_str.rfind("."):
            # European format: 10.500,45 -> 10500.45
            amount_str = amount_str.replace(".", "").replace(",", ".")
        else:
            # US/UK format: 10,500.45 -> 10500.45
            amount_str = amount_str.replace(",", "")
    elif "," in amount_str:
        parts = amount_str.split(",")
        is_zero_or_empty = not parts[0] or all(c == "0" for c in parts[0])
        # If the currency is known to use US/UK formatting, treat single comma as thousands separator unless it's a decimal
        if currency and currency not in EUROPEAN_STYLE_CURRENCIES:
            if len(parts[-1]) != 3 or is_zero_or_empty:
                amount_str = amount_str.replace(",", ".")
            else:
                amount_str = amount_str.replace(",", "")
        else:
            if len(parts[-1]) != 3 or is_zero_or_empty:
                # E.g. 10,50 or 0,050 -> likely European decimal
                amount_str = amount_str.replace(",", ".")
            else:
                # E.g. 10,500 -> likely thousands separator
                amount_str = amount_str.replace(",", "")
    elif "." in amount_str:
        parts = amount_str.split(".")
        is_zero_or_empty = not parts[0] or all(c == "0" for c in parts[0])
        # If the currency is known to use US/UK formatting, single dot is always a decimal separator
        if currency and currency not in EUROPEAN_STYLE_CURRENCIES:
            pass  # Do not strip the period
        elif currency in EUROPEAN_STYLE_CURRENCIES:
            if not is_zero_or_empty and (len(parts) > 2 or len(parts[-1]) == 3):
                # E.g. 10.000.000 or 10.500 -> European thousands separator
                amount_str = amount_str.replace(".", "")
        else:
            # Fallback when currency is not known/specified
            if not is_zero_or_empty and (len(parts) > 2 or len(parts[-1]) == 3):
                amount_str = amount_str.replace(".", "")

    return float(amount_str)


def extract_currency_matches(text):
    """
    Extracts currency mentions from a given text using regex and returns a list of
    (amount, currency_code) tuples.
    """
    matches = PATTERN.finditer(text)
    results = []

    for match in matches:
        try:
            # Check which side of the regex matched (amount first or currency first)
            if match.group(1) and match.group(3):
                # Format like: 100 USD, 1.5M EUR, 1.65 trillion dollars
                raw_currency = match.group(3)
                amount_str = match.group(1)
                suffix = match.group(2).lower() if match.group(2) else ""
            elif match.group(4) and match.group(5):
                # Format like: $100, €1.5M, $1.65 trillion, rs. 500
                raw_currency = match.group(4)
                amount_str = match.group(5)
                suffix = match.group(6).lower() if match.group(6) else ""
            else:
                continue

            raw_curr_lower = raw_currency.lower()
            if raw_curr_lower in SYMBOL_MAP:
                currency = SYMBOL_MAP[raw_curr_lower]
                currency_str = currency
            elif raw_currency in SYMBOL_MAP:
                currency = SYMBOL_MAP[raw_currency]
                currency_str = currency
            else:
                currency_str = raw_currency.upper()
                currency = currency_str

            amount = parse_amount(amount_str, currency)
        except ValueError:
            continue

        # Skip ambiguous 3-letter words if they are not matched via SYMBOL_MAP and are not uppercase
        if (
            currency_str in AMBIGUOUS_CURRENCIES
            and raw_curr_lower not in SYMBOL_MAP
            and not raw_currency.isupper()
        ):
            continue

        # Skip invalid 3-letter non-currency words (e.g. "him", "for", "the")
        valid_currencies = SUPPORTED_CURRENCIES or KNOWN_CURRENCIES
        if (
            raw_curr_lower not in SYMBOL_MAP
            and currency_str not in valid_currencies
            and not raw_currency.isupper()
        ):
            continue

        # Apply numeric multipliers (K, M, B, T, Trillion, Lakh, Crore, etc.)
        multiplier = MULTIPLIER_MAP.get(suffix, 1)
        amount *= multiplier

        # Ignore if currency is not supported by our API
        if SUPPORTED_CURRENCIES and currency not in SUPPORTED_CURRENCIES:
            continue

        results.append((amount, currency))

    return results


def format_number(num, format_pref):
    if num >= 10:
        s = f"{num:.2f}"
    else:
        s = f"{num:.4f}"

    if "." in s:
        s = s.rstrip("0").rstrip(".")

    parts = s.split(".")
    integer_part = parts[0]
    decimal_part = f".{parts[1]}" if len(parts) > 1 else ""

    if len(integer_part) > 3:
        if format_pref == "indian":
            res = integer_part[-3:]
            integer_part = integer_part[:-3]
            while len(integer_part) > 0:
                res = integer_part[-2:] + "," + res
                integer_part = integer_part[:-2]
            integer_part = res
        else:
            integer_part = f"{int(parts[0]):,}"

    return f"{integer_part}{decimal_part}"


def calculate_conversions(amount, currency, rates, chat_id):
    """
    Calculates the conversion of the given amount into the user's preferred
    target currencies and formats the output string for the bot to reply with.
    """
    # Fetch user preferences, falling back to defaults
    prefs = USER_PREFERENCES.get(chat_id, {})
    user_targets = prefs.get("targets", list(DEFAULT_TARGETS))
    format_pref = prefs.get("format", "international")

    targets = list(user_targets)

    # If the base currency is in their targets, remove it and potentially add a fallback
    if currency in targets:
        targets.remove(currency)
        if len(targets) < len(user_targets):
            if (
                FALLBACK_TARGET
                and FALLBACK_TARGET not in targets
                and FALLBACK_TARGET != currency
            ):
                targets.append(FALLBACK_TARGET)

    result_lines = []

    # Calculate conversions for up to 3 targets
    for target in targets[:3]:
        if target in rates:
            converted = amount * rates[target]
            converted_str = format_number(converted, format_pref)
            result_lines.append(f"{converted_str} {target}")

    # Build the final reply message
    if result_lines:
        amount_str = format_number(amount, format_pref)
        return f"<b>{amount_str} {currency}</b> equals:\n" + "\n".join(result_lines)

    return None
