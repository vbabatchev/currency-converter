import zmq

CURRENCY_SERVICE_ADDR = "ipc:///tmp/currency_converter"

context = zmq.Context()


def send_request(service_address: str, request: dict) -> dict:
    """Send a request to the service and return the response.

    :param service_address: the address of the service
    :request: the request payload to send
    :returns: the response from the service or an error message
    """
    with context.socket(zmq.REQ) as socket:
        try:
            socket.connect(service_address)
            socket.send_json(request)
            response = socket.recv_json()
            return response
        except zmq.ZMQError as error:
            print(f"Error connecting to the service: {error}")
            return {"error": "Service not available"}


def convert_currency(
    src_currency: str, tgt_currency: str, amt: float | int
) -> dict[str, str | float | int]:
    """Convert an amount from one currency to another.

    :param src_currency: the source currency code
    :param tgt_currency: the target currency code
    :param amt: the amount to convert
    :returns: the conversion result or an error message
    """
    request = {
        "action": "convert_currency",
        "data": {
            "source_currency": src_currency,
            "target_currency": tgt_currency,
            "amount": amt,
        },
    }
    response = send_request(CURRENCY_SERVICE_ADDR, request)
    return response


def get_exchange_rates(currency_code: str) -> dict[str, float | str]:
    """Get exchange rates for a specified currency code.

    :param currency_code: the currency code to get rates for
    :returns: the exchange rates or an error message
    """
    request = {"action": "get_exchange_rates", "data": {"currency_code": currency_code}}
    response = send_request(CURRENCY_SERVICE_ADDR, request)
    return response


def get_supported_currencies() -> dict[str, str]:
    """Get a list of supported currencies.

    :returns: the supported currencies or an error message
    """
    request = {"action": "get_supported_currencies"}
    response = send_request(CURRENCY_SERVICE_ADDR, request)
    return response


# Example usage
if __name__ == "__main__":
    print(convert_currency("USD", "EUR", 100.00))
    print(get_exchange_rates("USD"))
    print(get_supported_currencies())
