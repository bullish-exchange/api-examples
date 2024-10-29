import json
import os
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv
import marketdata_websocket

def main():
    load_dotenv()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="WebSocket client for orderbook data")
    parser.add_argument("-s", "--symbol", type=str, default="BTCUSDC", help="Symbol to subscribe to (default: BTCUSDC)")
    parser.add_argument("-d", "--duration", type=int, default=10, help="Duration of the subscription in seconds (default: 10)")
    parser.add_argument("-e", "--env", type=str, default="dev", choices=marketdata_websocket.env_urls.keys(), help="Environment to connect to (default: dev)")
    args = parser.parse_args()

    # Hardcoded URIs
    orderbook_uri = f"/trading-api/v1/market-data/orderbook"
    orderbook_test_uri = f"/trading-api/v1/market-data/orderbook-test"

    orderbook_data = []
    orderbook_test_data = []

    # Start threads for both connections with the specified duration
    marketdata_websocket.open_connection(args.env, orderbook_uri, orderbook_data, args.symbol, args.duration)
    marketdata_websocket.open_connection(args.env, orderbook_test_uri, orderbook_test_data, args.symbol, args.duration)

    # Let the main thread sleep for the duration to ensure the program doesn't exit prematurely
    time.sleep(args.duration)

    # Convert the list of JSON strings to JSON objects
    orderbook_data_objects = [json.loads(json_str) for json_str in orderbook_data]
    orderbook_test_data_objects = [json.loads(json_str) for json_str in orderbook_test_data]

    # Define the directory for storing files
    output_directory = f"recon/{args.env}/{args.symbol}"

    # Create the directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)

    # Get the current date and time for the file name
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Construct file names
    orderbook_file_name = f"{output_directory}/md_{current_time}_{args.duration}s_orderbook.json"
    orderbook_test_file_name = f"{output_directory}/md_{current_time}_{args.duration}s_orderbook-test.json"

    # Persist the data for comparison
    with open(orderbook_file_name, "w") as f:
        json.dump(orderbook_data_objects, f, indent=4)

    with open(orderbook_test_file_name, "w") as f:
        json.dump(orderbook_test_data_objects, f, indent=4)

    print("Data persisted for comparison.")

if __name__ == "__main__":
    main()

