import requests
from config import SUPPORTED_CURRENCIES


def init_supported_currencies():
    try:
        response = requests.get("https://open.er-api.com/v6/latest/USD")
        if response.status_code == 200:
            data = response.json()
            SUPPORTED_CURRENCIES.update(data.get("rates", {}).keys())
            return True
    except Exception as e:
        print(f"Error fetching currencies: {e}")
    return False


def get_exchange_rates(base_currency):
    try:
        response = requests.get(f"https://open.er-api.com/v6/latest/{base_currency}")
        if response.status_code == 200:
            return response.json().get("rates", {})
    except Exception as e:
        print(f"Error fetching rates for {base_currency}: {e}")
    return None
