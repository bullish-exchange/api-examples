import json
import os
from datetime import datetime, timezone
from hashlib import sha256
import requests
from eosio_signer import EOSIOKey
from dotenv import load_dotenv

load_dotenv()

HOST_NAME = os.getenv("BX_API_HOSTNAME")
PRIVATE_KEY = os.getenv("BX_PRIVATE_KEY")
JWT_TOKEN = os.getenv("BX_JWT")
AUTHORIZER = os.getenv("BX_AUTHORIZER")
TRADING_ACCOUNT_ID = os.getenv("BX_TRADING_ACCOUNT_ID")

LIQUIDITY_ID = "525143548447162376"
SYMBOL = "BTCUSD"
session = requests.Session()

response = session.get(HOST_NAME + "/trading-api/v1/nonce")
nonce = json.loads(response.text)["lowerBound"]
next_nonce = str(nonce + 1)
timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))

body = {
    "timestamp": timestamp,
    "nonce": next_nonce,
    "authorizer": AUTHORIZER,
    "command": {
        "commandType": "V2RemoveLiquidity",
        "liquidityId": LIQUIDITY_ID,
        "symbol": SYMBOL,
        "tradingAccountId": TRADING_ACCOUNT_ID,
    },
}

payload = (json.dumps(body, separators=(",", ":"))).encode("utf-8")
digest = sha256(payload.rstrip()).hexdigest()
eos_key = EOSIOKey(PRIVATE_KEY)
signature = eos_key.sign(digest)

headers = {
    "Content-type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}",
    "BX-SIGNATURE": signature,
    "BX-TIMESTAMP": timestamp,
    "BX-NONCE": next_nonce,
}

response = session.delete(
    HOST_NAME
    + "/trading-api/v1/amm-instructions"
    + f"?liquidityId={LIQUIDITY_ID}"
    + f"&symbol={SYMBOL}"
    + f"?tradingAccountId={TRADING_ACCOUNT_ID}",
    headers=headers,
)
print(f"HTTP Status: {response.status_code}, \n{response.text}")
