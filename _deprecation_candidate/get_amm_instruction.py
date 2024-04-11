import json
import math
import os
from datetime import datetime, timezone
from hashlib import sha256
import requests
from eosio_signer import EOSIOKey
from dotenv import load_dotenv

load_dotenv()

HOST_NAME = os.getenv("BX_API_HOSTNAME")
JWT_TOKEN = os.getenv("BX_JWT")

session = requests.Session()

params = {
    'symbol': 'BTCUSD',
    'status': 'OPEN',
}

headers = {
    "Content-type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}",
}

response = session.get(
    HOST_NAME + "/trading-api/v1/amm-instructions", params=params, headers=headers
)
print(f"HTTP Status: {response.status_code}, \n{response.text}")