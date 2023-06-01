import json
import os
import threading
import time

import websocket
from dotenv import load_dotenv

load_dotenv()

HOST_NAME = os.getenv("BX_WS_API_HOSTNAME")
JWT_TOKEN = os.getenv("BX_JWT")
COOKIE = f"JWT_COOKIE={JWT_TOKEN}"


def get_id():
    return str(int(time.time() * 1000))


def ping(conn):
    ping_message = {
        "jsonrpc": "2.0",
        "type": "command",
        "method": "keepalivePing",
        "params": {},
        "id": get_id()
    }
    conn.send(json.dumps(ping_message))
    threading.Timer(interval=5, function=ping, args=(conn,)).start()


def on_message(conn, message):
    print(f"Received message: {message}")


def on_error(conn, message):
    print(f"Received error: {message}")


def on_close(conn, close_status_code, close_msg):
    print(f"Closed connection to {conn.url}. close_status_code={close_status_code}, close_msg={close_msg}")


def on_open(conn):
    time.sleep(1)
    subscribe_message = {
        "jsonrpc": "2.0",
        "type": "command",
        "method": "subscribe",
        "params": {
            "topic": "l1Orderbook",
            "symbol": "BTCUSD"
        },
        "id": get_id()
    }
    conn.send(json.dumps(subscribe_message))


def open_connection():
    ws_conn = websocket.WebSocketApp(HOST_NAME + "/trading-api/v1/market-data",
                                     on_open=on_open,
                                     on_message=on_message,
                                     on_error=on_error,
                                     on_close=on_close,
                                     cookie=COOKIE)
    threading.Timer(interval=5, function=ping, args=(ws_conn,)).start()
    ws_conn.run_forever()


wst = threading.Thread(target=open_connection)
wst.start()
