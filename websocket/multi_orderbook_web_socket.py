import json
import os
import threading
import time

import websocket
from dotenv import load_dotenv

load_dotenv()

HOST_NAME = os.getenv("BX_WS_API_HOSTNAME")

## FOR EXAMPLE, WE ARE INTERESTED IN THE FOLLOWING ORDERBOOKS
btcusdc_l1 = {
    "topic": "l1Orderbook",
    "symbol": "BTCUSDC"
}

btcusdc_l2 = {
    "topic": "l2Orderbook",
    "symbol": "BTCUSDC"
}

ethusdc_l2 = {
    "topic": "l2Orderbook",
    "symbol": "ETHUSDC"
}

SUPSCRIPTIONS = [btcusdc_l1, btcusdc_l2, ethusdc_l2]

def on_open(conn):
    time.sleep(1)
    for sub in SUPSCRIPTIONS:
        topic = sub["topic"]
        symbol = sub["symbol"]

        # We need to send a subscribe message to the websocket for each topic and symbol we want
        subscribe_message = {
            "jsonrpc": "2.0",
            "type": "command",
            "method": "subscribe",
            "params": {
                "topic": topic,
                "symbol": symbol
            },
            "id": get_id()
        }

        print(f"Subscribing to topic:{topic} for symbol:{symbol}")
        conn.send(json.dumps(subscribe_message))

def get_id():
    return str(int(time.time() * 1000))

def on_message(conn, message):
    print(f"Received message: {message}")


def on_error(conn, message):
    print(f"Received error: {message}")

def on_close(conn, close_status_code, close_msg):
    print(f"Closed connection to {conn.url}. close_status_code={close_status_code}, close_msg={close_msg}")

def open_connection():
    ws_conn = websocket.WebSocketApp(HOST_NAME + "/trading-api/v1/market-data/orderbook",
                                     on_open=on_open,
                                     on_message=on_message,
                                     on_error=on_error,
                                     on_close=on_close)
    ws_conn.run_forever()


wst = threading.Thread(target=open_connection)
wst.start()
