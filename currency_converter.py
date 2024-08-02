"""
currency_converter.py

A simple currency conversion service that fetches exchange rates from
the FXRatesAPI and provides functionality to convert currencies, get
exchange rates, and list supported currencies.

This module performs the following tasks:
- Loads environment variables from a .env file using `dotenv`.
- Fetches and updates exchange rates from an external API.
- Provides currency conversion functionality.
- Responds to requests via a ZeroMQ (zmq) IPC socket.
- Periodically updates exchange rates using the `schedule` library.

Key Components:
- `fetch_exchange_rates(base: str)`
- `fetch_all_exchange_rates()`
- `schedule_thread()`
- `handle_convert_currency(data: dict)`
- `handle_get_exchange_rates(data: dict)`
- `handle_get_supported_currencies()`

The script initializes a ZeroMQ REP socket for IPC communication, starts
a background thread for scheduling tasks, and continuously processes
incoming messages until a shutdown signal is received.

Dependencies:
- `json`: For JSON data handling.
- `os`: For environment variable access.
- `urllib.request`: For making HTTP requests.
- `threading`: For concurrent execution of tasks.
- `time`: For sleep functionality.
- `schedule`: For scheduling periodic tasks.
- `zmq`: For ZeroMQ socket communication.
- `dotenv`: For loading environment variables from a .env file.
"""

import json
import os
import urllib.request
from threading import Event, Lock, Thread
from time import sleep

import schedule
import zmq
from dotenv import load_dotenv

load_dotenv()

SUPPORTED_CURRENCIES = {
    "USD": "United States Dollar",
    "EUR": "Euro",
    "JPY": "Japenese Yen",
    "GBP": "British Pound",
}

# FXRatesAPI configuration
FXRATES_API_URL = "https://api.fxratesapi.com/latest"
# Enter your own API key here
FXRATES_API_KEY = os.getenv("FXRATES_TOKEN")

if not FXRATES_API_KEY:
    raise EnvironmentError("FXRATES_TOKEN is not set in the environment variables")

exchange_rates = {}
exchange_rates_lock = Lock()
shutdown_event = Event()


def fetch_exchange_rates(base: str) -> dict | None:
    """Fetch exchange rates from the FXRatesAPI for a given base
    currency.

    :param base: string representation of the base currency code for which
                 which exchange rates are fetched
    :returns: a dictionary of exchange rates for the base currency if
             successfuly, otherwise None if there was an error
    """
    currencies = ",".join(filter(lambda x: x != base, SUPPORTED_CURRENCIES.keys()))
    try:
        url = f"{FXRATES_API_URL}?api_key={FXRATES_API_KEY}&currencies={currencies}&base={base}"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data.get("rates", {})
    except Exception as error:
        print(f"Failed to fetch exchange rates for {base}: {error}")
        return None


def fetch_all_exchange_rates():
    """Fetch exchange rates for all supported currencies and update the
    gloabl 'exchange_rates' dictionary.
    """
    global exchange_rates
    new_rates = {}
    for currency_code in SUPPORTED_CURRENCIES.keys():
        rates = fetch_exchange_rates(currency_code)
        if rates is not None:
            new_rates[currency_code] = rates

    with exchange_rates_lock:
        exchange_rates = new_rates

    print("Exchange rates updated.")


def schedule_thread():
    """Run a thread that periodically runs scheduled tasks."""
    while not shutdown_event.is_set():
        schedule.run_pending()
        sleep(1)


def handle_convert_currency(data: dict) -> dict:
    """Convert an amount from one currency to another using the current
    exchange rates.

    :param data: a dictionary containing 'source_currency',
                'target_currency', and 'amount'
    :returns: a dictionary containing the source and target currency
              codes, original amount, and converted amount, or an error
              message if conversion fails
    """
    source_currency = data.get("source_currency")
    target_currency = data.get("target_currency")
    amount = data.get("amount")

    if not isinstance(amount, (int, float)):
        return {"error": "Amount must be a number"}

    with exchange_rates_lock:
        if (
            source_currency not in exchange_rates
            or target_currency not in exchange_rates[source_currency]
        ):
            return {"error": "Invalid currency code"}

        exchange_rate = exchange_rates[source_currency].get(target_currency)
        if exchange_rate is None:
            return {"error": "Exchange rate not available"}

        converted_amount = amount * exchange_rate

    return {
        "source_currency": source_currency,
        "target_currency": target_currency,
        "amount": amount,
        "converted_amount": converted_amount,
    }


def handle_get_exchange_rates(data: dict) -> dict:
    """Retrieve exchange rates for a specified currency code.

    :param data: a dictionary containing 'currency_code'
    :returns: a dictionary of exchange rates for the specified currency
              or an error message if the code is invalid
    """
    currency_code = data.get("currency_code")

    if currency_code not in exchange_rates:
        return {"error": "Invalid currency code"}

    return exchange_rates[currency_code]


def handle_get_supported_currencies() -> dict[str, str]:
    """Retrieve a sorted list of supported currency codes and their
    corresponding names.

    :returns: a dictionary of supported currency codes and their
              corresponding names
    """
    sorted_currencies = dict(sorted(SUPPORTED_CURRENCIES.items()))
    return sorted_currencies


try:
    # Define server socket  using IPC
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("ipc:///tmp/currency_converter")

    # Populate exchange rates upon starting the service
    fetch_all_exchange_rates()

    # Schedule exchange rate updates every hour
    schedule.every().hour.do(fetch_all_exchange_rates)

    # Start the schedule thread
    scheduler_thread = Thread(target=schedule_thread, daemon=True)
    scheduler_thread.start()

    while not shutdown_event.is_set():
        try:
            message = socket.recv_json(flags=zmq.NOBLOCK)
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
        except zmq.Again:
            sleep(1)  # No message received, sleep briefly
        except Exception as e:
            print(f"Error: {e}")
            socket.send_json({"error": str(e)})

except KeyboardInterrupt:
    print("\nKeyboard interrupt received, shutting down...")
except Exception as e:
    print("Unexpected error: {e}")
finally:
    print("Cleaning up resources...")
    shutdown_event.set()
    # Wait for the scheduler thread to finish
    scheduler_thread.join()
    socket.setsockopt(zmq.LINGER, 0)
    socket.close()
    context.term()
    print("Service stopped.")
