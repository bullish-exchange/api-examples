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

# Global variable to store the keepalive timer
keepalive_timer = None

def send_keepalive(conn):
    """Send a keepAlive message to maintain the WebSocket connection"""
    global keepalive_timer
    
    if conn.sock and conn.sock.connected:
        keepalive_message = {
            "jsonrpc": "2.0",
            "type": "command",
            "method": "keepalivePing",
            "id": get_id()
        }
        
        print("Sending keepAlive message")
        conn.send(json.dumps(keepalive_message))
        
        # Schedule the next keepalive. Every 300 (5 minutes)
        keepalive_timer = threading.Timer(300, send_keepalive, [conn])
        keepalive_timer.daemon = True
        keepalive_timer.start()

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
        
    # Start the keepalive timer (5 minutes = 300 seconds)
    send_keepalive(conn)

def get_id():
    return str(int(time.time() * 1000))

def on_message(conn, message):
    print(f"Received message: {message}")

def on_error(conn, message):
    print(f"Received error: {message}")

def on_close(conn, close_status_code, close_msg):
    global keepalive_timer
    print(f"Closed connection to {conn.url}. close_status_code={close_status_code}, close_msg={close_msg}")
    
    # Cancel the keepalive timer if it exists
    if keepalive_timer:
        keepalive_timer.cancel()
        keepalive_timer = None

def open_connection():
    ws_conn = websocket.WebSocketApp(HOST_NAME + "/trading-api/v1/market-data/orderbook",
                                     on_open=on_open,
                                     on_message=on_message,
                                     on_error=on_error,
                                     on_close=on_close)
    ws_conn.run_forever()


wst = threading.Thread(target=open_connection)
wst.start()
