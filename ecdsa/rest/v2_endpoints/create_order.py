import base64
from datetime import timezone
from hashlib import sha256

import json
import os
import requests
import urllib3
from dotenv import load_dotenv
from ecdsa import SigningKey
from ecdsa.util import sigencode_der

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
JWT_TOKEN = os.getenv("BX_JWT")
TRADING_ACCOUNT_ID = os.getenv("BX_TRADING_ACCOUNT_ID")
RATELIMIT_TOKEN = os.getenv("BX_RATELIMIT_TOKEN")
URI = "/trading-api/v2/orders"

private_key_pem = """
-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgvaS39eOmvNWxkk0/
qvGg0tTRtcpv6pN0k3gSH2gfC62hRANCAAQ7bqWCgHHdaKRj2ZbmZIKi6sOKg+FT
vjW5Zm6UvsoN8cQbc+3mElZKwHBfs5vi+9h9JOBcRD9NF8Fz+Oa17yKV
-----END PRIVATE KEY-----
"""

# Decode the PEM-encoded private key
PRIVATE_KEY = SigningKey.from_pem(private_key_pem)

session = requests.Session()
response = session.get(HOST_NAME + "/trading-api/v1/nonce", verify=False)
nonce = json.loads(response.text)["lowerBound"]
next_nonce = str(int(datetime.now(timezone.utc).timestamp() * 1_000_000))
timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))

body = {
    "symbol": "ETHUSDC",
    "commandType": "V3CreateOrder",
    "type": "MARKET",
    "side": "SELL",
    "quantity": "1.123",
    "timeInForce": "GTC",
    "clientOrderId": next_nonce,
    "tradingAccountId": TRADING_ACCOUNT_ID,
}

body_string = json.dumps(body, separators=(",", ":"))
payload = (timestamp + next_nonce + "POST" + URI + body_string).encode("utf-8")
signature = PRIVATE_KEY.sign(payload, hashfunc=sha256, sigencode=sigencode_der)
signature = base64.b64encode(signature).decode()

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
