import hmac, requests, os, json
from datetime import datetime, timezone
from dotenv import load_dotenv
from hashlib import sha256

load_dotenv()

HOST_NAME = os.getenv("BX_API_HOSTNAME")
SECRET_KEY = bytes(os.getenv("BX_SECRET_KEY"), 'utf-8')
JWT_TOKEN = os.getenv("BX_JWT")
AUTHORIZER = os.getenv("BX_AUTHORIZER")

session = requests.Session()
response = session.get(HOST_NAME + "/trading-api/v1/nonce")
nonce = json.loads(response.text)["lowerBound"]
next_nonce = str(nonce + 1)
timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))
path = "/trading-api/v1/command"

body = {
    "timestamp": timestamp,
    "nonce": next_nonce,
    "authorizer": AUTHORIZER,
    "command": {
        "commandType": "V1TransferAsset",
        "assetSymbol": 'BTC',
        "quantity": '0.00010000',
        "fromTradingAccountId": SOURCE_ACCOUNT,
        "toTradingAccountId": TARGET_ACCOUNT,
    }
}

payload = (json.dumps(body, separators=(",", ":"))).encode('utf-8')
digest = sha256(payload).hexdigest()

print(f'Digest: {digest}')

signature = hmac.new(SECRET_KEY, digest.encode('utf-8'), sha256).hexdigest()

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer %s" % JWT_TOKEN,
    "BX-SIGNATURE": signature,
    "BX-TIMESTAMP": timestamp,
    "BX-NONCE": next_nonce,
}

response = session.post(
    HOST_NAME + path, headers=headers, params={'commandType': 'V1TransferAsset'}, data=payload, # json=body,
)
print(f"HTTP Status: {response.status_code}, \n{response.text}")