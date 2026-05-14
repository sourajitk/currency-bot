from .config import (
    PATTERN,
    SYMBOL_MAP,
    SUPPORTED_CURRENCIES,
    USER_PREFERENCES,
    DEFAULT_TARGETS,
    FALLBACK_TARGET,
)

def extract_currency_matches(text):
    matches = PATTERN.finditer(text)
    results = []
    for match in matches:
        if match.group(1) and match.group(3):
            amount = float(match.group(1))
            suffix = match.group(2).lower() if match.group(2) else ""
            currency_str = match.group(3).upper()
        elif match.group(4) and match.group(5):
            currency_str = match.group(4).upper()
            amount = float(match.group(5))
            suffix = match.group(6).lower() if match.group(6) else ""
        else:
            continue

        multiplier = 1
        if suffix == 'k': multiplier = 1_000
        elif suffix == 'l': multiplier = 100_000
        elif suffix == 'm': multiplier = 1_000_000
        elif suffix == 'cr': multiplier = 10_000_000
        elif suffix == 'b': multiplier = 1_000_000_000
        elif suffix == 't': multiplier = 1_000_000_000_000
        
        amount *= multiplier

        currency = SYMBOL_MAP.get(currency_str, currency_str)
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
    prefs = USER_PREFERENCES.get(chat_id, {})
    user_targets = prefs.get("targets", list(DEFAULT_TARGETS))
    format_pref = prefs.get("format", "international")

    targets = list(user_targets)
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
    for target in targets[:3]:
        if target in rates:
            converted = amount * rates[target]
            converted_str = format_number(converted, format_pref)
            result_lines.append(f"{converted_str} {target}")

    if result_lines:
        amount_str = format_number(amount, format_pref)
        return f"<b>{amount_str} {currency}</b> equals:\n" + "\n".join(result_lines)
    return None
