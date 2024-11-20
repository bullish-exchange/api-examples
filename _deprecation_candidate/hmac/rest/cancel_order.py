import hmac, requests, os, json
from datetime import datetime
from dotenv import load_dotenv
from hashlib import sha256

load_dotenv()

HOST_NAME = os.getenv("BX_API_HOSTNAME")
SECRET_KEY = bytes(os.getenv("BX_SECRET_KEY"), 'utf-8')
JWT_TOKEN = os.getenv("BX_JWT")
AUTHORIZER = os.getenv("BX_AUTHORIZER")

ORDER_ID = "399014193334321153"
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
        "commandType": "V1CancelOrder",
        "orderId": ORDER_ID,
        "handle": None,
        "symbol": SYMBOL,
    },
}

payload = (json.dumps(body, separators=(",", ":"))).encode("utf-8")
digest = sha256(payload).hexdigest().encode('utf-8')
signature = hmac.new(SECRET_KEY, digest, sha256).hexdigest()

headers = {
    "Content-type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}",
    "BX-SIGNATURE": signature,
    "BX-TIMESTAMP": timestamp,
    "BX-NONCE": next_nonce,
}

response = session.delete(
    HOST_NAME
    + "/trading-api/v1/orders"
    + f"?orderId={ORDER_ID}"
    + f"&symbol={SYMBOL}",
    headers=headers,
)
print(f"HTTP Status: {response.status_code}, \n{response.text}")
