import base64
import json
import os
from datetime import datetime, timezone
from hashlib import sha256

import requests
from eosio_signer import EOSIOKey

HOST_NAME = os.getenv("BX_API_HOSTNAME")
PUBLIC_KEY = os.getenv("BX_PUBLIC_KEY")
PRIVATE_KEY = os.getenv("BX_PRIVATE_KEY")
ENCODED_METADATA = os.getenv("BX_API_METADATA")

session = requests.Session()
metadata = base64.b64decode(ENCODED_METADATA)
account_id = str(json.loads(metadata)["accountId"])

timestamp = int(datetime.now(timezone.utc).timestamp())
expiration_time = int(timestamp + 300)
login_payload = {
    "accountId": account_id,
    "nonce": timestamp,
    "expirationTime": expiration_time,
    "biometricsUsed": False,
    "sessionKey": None,
}

payload = (json.dumps(login_payload, separators=(",", ":"))).encode("utf-8")
digest = sha256(payload.rstrip()).hexdigest()
eos_key = EOSIOKey(PRIVATE_KEY)
signature = eos_key.sign(digest)

headers = {
    "Content-type": "application/json",
}
body = {
    "publicKey": PUBLIC_KEY,
    "signature": signature,
    "loginPayload": login_payload,
}

response = session.post(
    HOST_NAME + "/trading-api/v1/users/login",
    json=body,
    headers=headers,
)
print(f"HTTP Status: {response.status_code}, \n{response.text}")
