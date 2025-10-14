import hmac
import json
import os
import requests
from datetime import timezone
from hashlib import sha256
import time

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
URI = "/trading-api/v2/mmp-configuration"

session = requests.Session()

def create_hmac_signature(method, uri, body=None):
    timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))
    next_nonce = str(int(datetime.now(timezone.utc).timestamp() * 1_000_000))
    
    body_string = ""
    if body:
        body_string = json.dumps(body, separators=(",", ":"))
    
    payload = timestamp + next_nonce + method + uri + body_string
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
    return headers, body_string

body = {
  "commandType": "V1SetMMP",
  "tradingAccountId": str(TRADING_ACCOUNT_ID),
  "underlyingAssetSymbol": "BTC",
  "windowTimeInSeconds": "10",
  "frozenTimeInSeconds": "5",
  "quantityLimit": "1000.2",
  "deltaLimit": "1000.1"
}

# Send the MMP request. If there is a prior MMP config, this will have no effect
headers, body_string = create_hmac_signature("POST", URI, body)
response = session.post(
    HOST_NAME + URI, data=body_string, headers=headers
)
print("====== POST => Prep ====")
logging.info(f"http_status={response.status_code} body={response.text}")

body_reset = {
  "commandType": "V1ResetMMP",
  "tradingAccountId": str(TRADING_ACCOUNT_ID),
  "underlyingAssetSymbol": "BTC"
}
# Send the MMP reset command. The next set MMP config will then take effect
headers, body_string = create_hmac_signature("POST", URI, body_reset)
print("====== POST => Reset ====")
response = session.post(
    HOST_NAME + URI, data=body_string, headers=headers
)
logging.info(f"http_status={response.status_code} body={response.text}")

time.sleep(1)

# Send the MMP request. This will take effect
headers, body_string = create_hmac_signature("POST", URI, body)
response = session.post(
    HOST_NAME + URI, data=body_string, headers=headers
)
print("====== POST => Actual ====")
logging.info(f"http_status={response.status_code} body={response.text}")

time.sleep(1)

get_headers, _ = create_hmac_signature("GET", URI)
get_params = {"tradingAccountId": str(TRADING_ACCOUNT_ID)}
get_response = session.get(HOST_NAME + URI, params=get_params, headers=get_headers)
print("====== GET ====")
print(get_response.text)
