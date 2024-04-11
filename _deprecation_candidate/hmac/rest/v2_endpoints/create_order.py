import hmac
import json
import os
import requests
from datetime import timezone
from hashlib import sha256

import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
from datetime import datetime
import logging
import sys
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s | %(levelname)-4s | %(threadName)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.StreamHandler(sys.stdout)])

HOST_NAME = os.getenv("BX_API_HOSTNAME")
SECRET_KEY = bytes(os.getenv("BX_SECRET_KEY"), 'utf-8')
JWT_TOKEN = os.getenv("BX_JWT")
TRADING_ACCOUNT_ID = os.getenv("BX_TRADING_ACCOUNT_ID")
RATELIMIT_TOKEN = os.getenv("BX_RATELIMIT_TOKEN")
URI = "/trading-api/v2/orders"

session = requests.Session()
response = session.get(HOST_NAME + "/trading-api/v1/nonce", verify=False)
nonce = json.loads(response.text)["lowerBound"]
next_nonce = str(int(datetime.now(timezone.utc).timestamp() * 1_000_000))
timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))

body = {
    "symbol": "ETHUSDC",
    "commandType": "V3CreateOrder",
    "type": "LIMIT",
    "side": "SELL",
    "quantity": "1.123",
    "price": "1432.6",
    "timeInForce": "GTC",
    "allowBorrow": False,
    "clientOrderId": next_nonce,
    "tradingAccountId": TRADING_ACCOUNT_ID,
}

body_string = json.dumps(body, separators=(",", ":"))
payload = timestamp + next_nonce + "POST" + URI + body_string
digest = sha256(payload.encode("utf-8")).hexdigest().encode('utf-8')
signature = hmac.new(SECRET_KEY, digest, sha256).hexdigest()

headers = {
    "Content-type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}",
    "BX-SIGNATURE": signature,
    "BX-TIMESTAMP": timestamp,
    "BX-NONCE": next_nonce,
    "BX-RATELIMIT-TOKEN": f"{RATELIMIT_TOKEN}"
}

response = session.post(
    HOST_NAME + URI, data=body_string, headers=headers
)
logging.info(f"http_status={response.status_code} body={response.text}")
