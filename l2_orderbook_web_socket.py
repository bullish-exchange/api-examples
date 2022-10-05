import json
import os
import threading
import time

import websocket

WS_HOST_NAME = os.getenv("BX_WS_API_HOSTNAME")
BIDS = {}
ASKS = {}
SEQ_NUM = None
IS_FIRST_CONFLATED_MESSAGE = True


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


def update_price_level(new_price_levels, current_price_levels):
    for i in range(0, len(new_price_levels), 2):
        price = new_price_levels[i]
        qty = new_price_levels[i + 1]
        if float(qty) == 0 and price in current_price_levels:
            current_price_levels.pop(price)
        else:
            current_price_levels[price] = qty


def validate_seq_num(conn, seq_num_range):
    global IS_FIRST_CONFLATED_MESSAGE, SEQ_NUM
    if IS_FIRST_CONFLATED_MESSAGE:
        if seq_num_range[0] <= SEQ_NUM + 1 and SEQ_NUM <= seq_num_range[1]:
            IS_FIRST_CONFLATED_MESSAGE = False
            SEQ_NUM = seq_num_range[1]
        else:
            print(f"Sequence out of order. current={SEQ_NUM}, received={seq_num_range[0]}")
            conn.close()
    elif seq_num_range[0] != SEQ_NUM + 1:
        print(f"Sequence out of order. expected={SEQ_NUM + 1}, received={seq_num_range[0]}")
        conn.close()


def on_message(conn, message):
    global BIDS, ASKS, SEQ_NUM, IS_FIRST_CONFLATED_MESSAGE
    message = json.loads(message)
    if "type" not in message:
        return
    data = message["data"]
    bids = data["bids"]
    asks = data["asks"]
    seq_num_range = data["sequenceNumberRange"]
    if SEQ_NUM is not None:
        validate_seq_num(conn, seq_num_range)
    SEQ_NUM = seq_num_range[1]
    if message["type"] == "snapshot":
        BIDS, ASKS = {}, {}
    update_price_level(bids, BIDS)
    update_price_level(asks, ASKS)
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
