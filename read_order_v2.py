import json
import os

import requests

HOST_NAME = os.getenv("BX_API_HOSTNAME")
JWT_TOKEN = os.getenv("BX_JWT")
TRADING_ACCOUNT_ID = os.getenv("BX_TRADING_ACCOUNT_ID")
session = requests.Session()

headers = {
    "Content-type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}",
}

response = session.get(
    HOST_NAME
    + "/trading-api/v1/orders"
    + f"?tradingAccountId={TRADING_ACCOUNT_ID}",
    headers=headers,
    )
response_json = json.dumps(response.json(), indent=2)
print(f"HTTP Status: {response.status_code}, \n{response_json}")
