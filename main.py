import os
import telebot
from dotenv import load_dotenv

from config import (
    USER_PREFERENCES,
    DEFAULT_TARGETS,
    SUPPORTED_CURRENCIES,
    save_preferences,
)
from api import init_supported_currencies, get_exchange_rates
from logic import extract_currency_matches, calculate_conversions

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_token_here":
    print("Please set TELEGRAM_BOT_TOKEN in your .env file.")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    help_text = (
        "Hello! I am a Currency Converter Bot. Just send me a message like '1000 INR' or '$50' and I will convert it for you.\n\n"
        "Configuration Commands:\n"
        "/config — See your current settings.\n"
        "/config set USD EUR JPY — Replace the list of currencies (max 3).\n"
        "/config add GBP — Add a new currency.\n"
        "/config remove AED — Remove a currency.\n"
        "/config format intl — Use international format (1,000,000).\n"
        "/config format indian — Use Indian format (10,00,000)."
    )
    bot.reply_to(message, help_text)


@bot.message_handler(commands=["config"])
def config_currencies(message):
    args = message.text.split()[1:]

    if message.chat.id not in USER_PREFERENCES:
        USER_PREFERENCES[message.chat.id] = {
            "targets": list(DEFAULT_TARGETS),
            "format": "international",
        }

    prefs = USER_PREFERENCES[message.chat.id]
    current = prefs.get("targets", list(DEFAULT_TARGETS))
    current_fmt = prefs.get("format", "international")

    if not args:
        bot.reply_to(
            message,
            f"Current Currencies: {', '.join(current)}\nFormat: {current_fmt}\n\nUse /help to see how to change these.",
        )
        return

    action = args[0].lower()

    if action == "format":
        if len(args) < 2:
            bot.reply_to(message, "Please provide a format: 'intl' or 'indian'")
            return
        fmt_arg = args[1].lower()
        if fmt_arg in ["intl", "international", "millions"]:
            prefs["format"] = "international"
            bot.reply_to(message, "Number format set to International (e.g. 1,000,000)")
        elif fmt_arg in ["indian", "lakhs", "crores"]:
            prefs["format"] = "indian"
            bot.reply_to(message, "Number format set to Indian (e.g. 10,00,000)")
        else:
            bot.reply_to(message, "Unknown format. Use 'intl' or 'indian'.")
        save_preferences(USER_PREFERENCES)
        return

    currencies = [c.upper() for c in args[1:]]

    if action not in ["set", "add", "remove"] or not currencies:
        bot.reply_to(
            message,
            "Please provide an action and currency codes. Example: /config add USD",
        )
        return

    for curr in currencies:
        if SUPPORTED_CURRENCIES and curr not in SUPPORTED_CURRENCIES:
            bot.reply_to(message, f"Currency {curr} is not supported.")
            return

    if action == "set":
        prefs["targets"] = currencies[:3]
        bot.reply_to(
            message,
            f"Your output currencies have been set to: {', '.join(prefs['targets'])} (max 3)",
        )
    elif action == "add":
        for c in currencies:
            if c in current:
                current.remove(c)
            current.append(c)
        prefs["targets"] = current[-3:]
        bot.reply_to(
            message,
            f"Your output currencies have been updated to: {', '.join(prefs['targets'])} (max 3)",
        )
    elif action == "remove":
        for c in currencies:
            if c in current:
                current.remove(c)
        if not current:
            current = list(DEFAULT_TARGETS)
            bot.reply_to(
                message,
                f"Cannot remove all currencies. Resetting to default: {', '.join(current)}",
            )
        else:
            bot.reply_to(
                message,
                f"Your output currencies have been updated to: {', '.join(current)}",
            )
        prefs["targets"] = current

    save_preferences(USER_PREFERENCES)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    matches = extract_currency_matches(text)
    conversions = []

    for amount, currency in matches:
        rates = get_exchange_rates(currency)
        if rates:
            conversion_text = calculate_conversions(
                amount, currency, rates, message.chat.id
            )
            if conversion_text:
                conversions.append(conversion_text)

    if conversions:
        reply_text = "\n\n".join(conversions)
        bot.reply_to(message, reply_text, parse_mode="HTML")


if __name__ == "__main__":
    if init_supported_currencies():
        print("Bot is running...")
        bot.polling(none_stop=True)
    else:
        print("Failed to initialize supported currencies.")
