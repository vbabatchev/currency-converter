import zmq

CURRENCY_SERVICE_ADDR = "ipc:///tmp/currency_converter"

context = zmq.Context()


def send_request(service_address, request):
    socket = context.socket(zmq.REQ)
    try:
        socket.connect(service_address)
        socket.send_json(request)
        response = socket.recv_json()
        return response
    except zmq.ZMQError as error:
        print(f"Error connecting to the service: {error}")
        return {"error": "Service not available"}
    finally:
        socket.close()


def convert_currency(src_currency, tgt_currency, amt):
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


def get_exchange_rates(currency_code):
    request = {"action": "get_exchange_rates", "data": {"currency_code": currency_code}}
    response = response = send_request(CURRENCY_SERVICE_ADDR, request)
    return response


def get_supported_currencies():
    request = {"action": "get_supported_currencies"}
    response = response = send_request(CURRENCY_SERVICE_ADDR, request)
    return response


print(convert_currency("USD", "EUR", 100.00))
print(get_exchange_rates("USD"))
print(get_supported_currencies())
