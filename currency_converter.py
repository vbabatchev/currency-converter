import json
import urllib.request

import schedule
import zmq

from threading import Thread
from time import sleep

SUPPORTED_CURRENCIES = {
    "USD": "United States Dollar",
    "EUR": "Euro",
    "JPY": "Japenese Yen",
    "GBP": "British Pound",
}

# FXRatesAPI configuration
FXRATES_API_URL = "https://api.fxratesapi.com/latest"
# Enter your own API key here
FXRATES_API_KEY = "fxr_live_307dded1f0e5e27ec42658f771b15698d130"

# Define server socket  using IPC
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("ipc:///tmp/currency_converter")


def fetch_exchange_rates(base):
    currencies = ",".join(filter(lambda x: x != base, SUPPORTED_CURRENCIES.keys()))
    rates = {}
    try:
        url = f"{FXRATES_API_URL}?api_key={FXRATES_API_KEY}&currencies={currencies}&base={base}"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            base_currency = data.get("base")
            rates = data.get("rates")
    except Exception as error:
        print(f"Failed to fetch exchange rates: {error}")
    finally:
        return rates


def fetch_all_exchange_rates():
    exchange_rates = {}
    for currency_code in SUPPORTED_CURRENCIES.keys():
        exchange_rates[currency_code] = fetch_exchange_rates(currency_code)
    return exchange_rates


# Populate exchange rates upon starting the service
exchange_rates = fetch_all_exchange_rates()

# Schedule exchange rate updates every hour
schedule.every().hour.do(fetch_all_exchange_rates)


def schedule_thread():
    while True:
        schedule.run_pending()
        sleep(1)


# Start the schedule thread
Thread(target=schedule_thread, daemon=True).start()


def handle_convert_currency(data):
    source_currency = data.get("source_currency")
    target_currency = data.get("target_currency")
    amount = data.get("amount")

    if (
        source_currency not in exchange_rates
        or target_currency not in exchange_rates[source_currency]
    ):
        return {"error": "Invalid currency code"}

    exchange_rate = exchange_rates[source_currency][target_currency]
    converted_amount = amount * exchange_rate
    return {
        "source_currency": source_currency,
        "target_currency": target_currency,
        "amount": amount,
        "converted_amount": converted_amount,
    }


def handle_get_exchange_rates(data):
    currency_code = data.get("currency_code")

    if currency_code not in exchange_rates:
        return {"error": "Invalid currency code"}

    return exchange_rates[currency_code]


def handle_get_supported_currencies() -> dict[str, str]:
    sorted_currencies = dict(sorted(SUPPORTED_CURRENCIES.items()))
    return sorted_currencies


while True:
    try:
        message = socket.recv_json()
        action = message.get("action")
        data = message.get("data")
        if action == "convert_currency":
            response = handle_convert_currency(data)
        elif action == "get_exchange_rates":
            response = handle_get_exchange_rates(data)
        elif action == "get_supported_currencies":
            response = handle_get_supported_currencies()
        else:
            response = {"error": "Unknown action"}

        socket.send_json(response)
    except Exception as e:
        print(f"Error: {e}")
