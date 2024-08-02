import zmq
import urllib.request
import json

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

exchange_rates = {}


def fetch_exchange_rates():
    try:
        for base in SUPPORTED_CURRENCIES.keys():
            currencies = ",".join(
                filter(lambda x: x != base, SUPPORTED_CURRENCIES.keys())
            )
            url = f"{FXRATES_API_URL}?api_key={FXRATES_API_KEY}&currencies={currencies}&base={base}"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                base_currency = data.get("base")
                rates = data.get("rates")

                global exchange_rates
                exchange_rates[base_currency] = rates
    except Exception as error:
        print(f"Failed to fetch exchange rates: {error}")
    else:
        print("Exchange rates updated")


def handle_get_exchange_rates(data):
    currency_code = data.get("currency_code")

    if currency_code not in exchange_rates:
        return {"error": "Invalid currency code"}

    return exchange_rates[currency_code]
