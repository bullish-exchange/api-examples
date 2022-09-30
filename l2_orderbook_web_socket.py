import json
import os
import threading
import time

import websocket

WS_HOST_NAME = os.getenv("BX_WS_API_HOSTNAME")
BIDS = {}
ASKS = {}
SEQ_NUM = None


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
    global BIDS, ASKS, SEQ_NUM
    message = json.loads(message)
    if "type" not in message:
        return
    data = message["data"]
    bids = data["bids"]
    asks = data["asks"]
    seq_num_range = data["sequenceNumberRange"]
    if message["type"] == "snapshot":
        if SEQ_NUM is not None:
            if seq_num_range[0] != SEQ_NUM + 1:
                print(f"Sequence out of order. expected={SEQ_NUM + 1}, received={seq_num_range[0]}")
                conn.close()
        SEQ_NUM = seq_num_range[1]
        BIDS, ASKS = {}, {}
    if message["type"] == "update":
        if seq_num_range[0] != SEQ_NUM + 1:
            print(f"Sequence out of order. expected={SEQ_NUM + 1}, received={seq_num_range[0]}")
            conn.close()
        SEQ_NUM = seq_num_range[1]
    for i in range(0, len(bids), 2):
        price = bids[i]
        qty = bids[i + 1]
        if float(qty) == 0:
            BIDS.pop(price)
        else:
            BIDS[price] = qty
    for i in range(0, len(asks), 2):
        price = asks[i]
        qty = asks[i + 1]
        if float(qty) == 0:
            ASKS.pop(price)
        else:
            ASKS[price] = qty
    BIDS = dict(sorted(BIDS.items(), key=lambda price_level: float(price_level[0]), reverse=True))
    ASKS = dict(sorted(ASKS.items(), key=lambda price_level: float(price_level[0])))


def on_error(conn, message):
    print(f"Received error: {message}")


def on_close(conn, close_status_code, close_msg):
    print(f"Closed connection to {conn.url}. close_status_code={close_status_code}, close_msg={close_msg}")


def open_connection():
    ws_conn = websocket.WebSocketApp(WS_HOST_NAME + "/trading-api/markets/BTCUSD/orderbook/hybrid",
                                     on_message=on_message,
                                     on_error=on_error,
                                     on_close=on_close)
    threading.Timer(interval=5, function=ping, args=(ws_conn,)).start()
    ws_conn.run_forever()


wst = threading.Thread(target=open_connection)
wst.start()
