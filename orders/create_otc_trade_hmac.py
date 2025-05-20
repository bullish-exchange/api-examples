import hmac
import json
import logging
import os
import requests
import sys
from datetime import datetime
from datetime import timezone
from dotenv import load_dotenv
from hashlib import sha256

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s | %(levelname)-4s | %(threadName)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.StreamHandler(sys.stdout)])

HOST_NAME = os.getenv("BX_API_HOSTNAME")
SECRET_KEY = bytes(os.getenv("BX_SECRET_KEY"), 'utf-8')
JWT_TOKEN = os.getenv("BX_JWT")
TRADING_ACCOUNT_ID = os.getenv("BX_TRADING_ACCOUNT_ID")
PATH = "/trading-api/v2/otc-trades"

session = requests.Session()
response = session.get(HOST_NAME + "/trading-api/v1/nonce", verify=False)
nonce = json.loads(response.text)["lowerBound"]
next_nonce = str(int(datetime.now(timezone.utc).timestamp() * 1_000_000))
timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))

body = {
    "commandType": "V1CreateOtcTrade",
    "sharedMatchKey": "2025may19match001",
    "clientOtcTradeId": "20250519001",
    "tradingAccountId": TRADING_ACCOUNT_ID,
    "isTaker": False,
    "memo": "create otc trade HMAC",
    "trades": [
        {
            "symbol": "SOL-USDC-PERP",
            "side": "SELL",
            "price": "130",
            "quantity": "1.0000"
        },{
            "symbol": "BTC-USDC-20250829",
            "side": "BUY",
            "price": "52669.3",
            "quantity": "0.25"
        }
    ]
}

body_string = json.dumps(body, separators=(",", ":"))
# the extra replace() call is because memo field can contain spaces
payload = (timestamp + next_nonce + "POST" + PATH + body_string.replace(" ", "")).encode("utf-8")
digest = sha256(payload).hexdigest().encode('utf-8')
signature = hmac.new(SECRET_KEY, digest, sha256).hexdigest()

headers = {
    "Content-type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}",
    "BX-SIGNATURE": signature,
    "BX-TIMESTAMP": timestamp,
    "BX-NONCE": next_nonce
}

logging.info(f"headers=\n{json.dumps(headers, indent=2)}")
logging.info(f"body=\n{json.dumps(body, indent=2)}")

url = HOST_NAME + PATH
response = session.post(
    url, data=body_string, headers=headers
)
formatted_response = json.dumps(json.loads(response.text), indent=2)
logging.info(f"http_status={response.status_code} body=\n{formatted_response}")
