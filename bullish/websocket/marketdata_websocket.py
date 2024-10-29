import json
import threading
import websocket

# Environment URLs
env_urls = {
    "prod": "wss://api.exchange.bullish.com",
    "simnext": "wss://api.simnext.bullish-test.com",
    "uat": "wss://api.uat.vdevel.net",
    "dev": "wss://cornea.hadev.vdevel.net"
}

def get_id():
    import time
    return str(int(time.time() * 1000))

def on_message(conn, message, storage):
    print(f"Received message from {conn.url}: {message}")
    storage.append(message)  # Store the raw JSON string

def on_error(conn, message):
    print(f"Received error from {conn.url}: {message}")

def on_close(conn, close_status_code, close_msg):
    print(f"Closed connection to {conn.url}. close_status_code={close_status_code}, close_msg={close_msg}")

def on_open(conn, symbol):
    import time
    time.sleep(1)
    subscribe_message = {
        "jsonrpc": "2.0",
        "type": "command",
        "method": "subscribe",
        "params": {
            "topic": "l2Orderbook",
            "symbol": symbol
        },
        "id": get_id()
    }
    print(f"sending subscribe msg to {conn.url}: {subscribe_message}")
    conn.send(json.dumps(subscribe_message))

def open_connection(env, uri, storage, symbol, duration):
    hostname = env_urls[env]
    full_uri = f"{hostname}{uri}"

    ws_conn = websocket.WebSocketApp(full_uri,
                                     on_open=lambda conn: on_open(conn, symbol),
                                     on_message=lambda conn, msg: on_message(conn, msg, storage),
                                     on_error=on_error,
                                     on_close=on_close)

    def run():
        ws_conn.run_forever()

    # Start the WebSocket connection in a separate thread
    ws_thread = threading.Thread(target=run)
    ws_thread.start()

    # Schedule the connection to close after the specified duration
    threading.Timer(duration, ws_conn.close).start()
