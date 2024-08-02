# Currency Converter Microservice

This microservice provides currency conversion functionality. It fetches exchange rates from an external provider upon start 
and updates them hourly. The service handles conversion requests using pre-fetched exchange rates.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Running the Service](#running-the-service)
4. [Communication Contract](#communication-contract)
    - [Requesting Data](#requesting-data)
    - [Receiving Data](#receiving-data)
    - [Example Call](#example-call)

## Prerequisites

- Python 3 must be installed. You can download it from the [official website](https://www.python.org/downloads/).

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/vbabatchev/currency-converter-microservice.git
    cd currency-converter-microservice
    ```

2. **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Service

Go to [FXRatesAPI](https://fxratesapi.com/) to get access token.

1. **Create a .env file and set exchange rate provider API key:**
    ```bash
    echo 'FXRATES_TOKEN="your_api_key"' > .env # On Windows use 'echo FXRATES_TOKEN="your_api_key" > .env'

    ```

2. **Start the currency converter microservice:**
    ```bash
    python currency_converter_service.py
    ```

## Communication Contract

### Requesting Data

To request data from the currency converter microservice, send a JSON request to the appropriate ZeroMQ socket connected to the service address `"ipc:///tmp/currency_converter"`.

#### Request Parameters

**Action:** Specifies the action to be performed.

- `convert_currency`
- `get_exchange_rates` 
- `get_supported_currencies`

**Data:** Contains the necessary parameters for the action.

| convert_currency   | get_exchange_rates |
| ------------------ | ------------------ |
| `source_currency`  | `currency_code`    |
| `target_currency`  |                    |
| `amount`           |                    |


#### Example Conversion Request
```json
{
  "action": "convert_currency",
  "data": {
    "source_currency": "USD",
    "target_currency": "EUR",
    "amount": 100.00
  }
}
```

#### Example Exchange Rate Request
```json
{
  "action": "get_exchange_rates",
  "data": {
    "currency_code": "USD"
  }
}
```

#### Example Supported Currencies Request
```json
{
  "action": "get_supported_currencies"
}
```

### Receiving Data

The microservice will respond with a JSON object containing the result of the requested action.

#### Example Conversion Response
```json
{
  "source_currency": "USD",
  "target_currency": "EUR",
  "amount": 100.00,
  "converted_amount": 92.60101824
}
```

#### Example Exchange Rate Response
```json
{
  "EUR": 0.9260101824, 
  "GBP": 0.7857401541, 
  "JPY": 149.4001148141
}
```

#### Example Supported Currencies Response
```json
{
  "EUR": "Euro", 
  "GBP": "British Pound", 
  "JPY": "Japenese Yen", 
  "USD": "United States Dollar"
}
```

#### Example Error Response
```json
{
  "error": "Invalid currency code"
}
```

### Example Conversion Call
```python
import zmq

context = zmq.Context()

# Connect to the currency converter service
socket = context.socket(zmq.REQ)
socket.connect("ipc:///tmp/currency_converter")

# Prepare the request
request = {
    "action": "convert_currency",
    "data": {
        "source_currency": "USD",
        "target_currency": "EUR",
        "amount": 100.00
    }
}

# Send the request
socket.send_json(request)

# Receive the response
response = socket.recv_json()

# Display conversion rounded to the appropriate precision for your task
print("Converted Amount:", round(response["converted_amount"], 2))
```

