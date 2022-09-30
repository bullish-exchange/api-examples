import json
import os
import ssl
import threading
import time
from collections import deque

import websocket

WS_HOST_NAME = os.getenv("BX_WS_API_HOSTNAME")
TRADES = None
CURR_TRADE_ID = None


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
    global TRADES, CURR_TRADE_ID
    message = json.loads(message)
    if "type" not in message:
        return
    print(message)
    data = message["data"]
    if message["type"] == "snapshot" and isinstance(data, list):
        if data:
            CURR_TRADE_ID = data[0]["tradeId"]
            TRADES = deque(data, maxlen=100)
        else:
            TRADES = deque(maxlen=100)
    if message["type"] == "update":
        trade_id = data["tradeId"]
        if trade_id > CURR_TRADE_ID:
            TRADES.appendleft(data)
            CURR_TRADE_ID = data["tradeId"]
        else:
            print(f"Incoming trade_id must be larger than current trade_id. trade_id={trade_id} curr_trade_id={CURR_TRADE_ID}")
            conn.close()


def on_error(conn, message):
    print(f"Received error: {message}")


def on_close(conn, close_status_code, close_msg):
    print(f"Closed connection to {conn.url}. close_status_code={close_status_code}, close_msg={close_msg}")


def open_connection():
    ws_conn = websocket.WebSocketApp(WS_HOST_NAME + "/trading-api/v1/market-data/trades/BTCUSD",
                                     on_message=on_message,
                                     on_error=on_error,
                                     on_close=on_close)
    threading.Timer(interval=5, function=ping, args=(ws_conn,)).start()
    ws_conn.run_forever()


wst = threading.Thread(target=open_connection)
wst.start()
