import base64
import json
import os
from datetime import datetime, timezone
from hashlib import sha256
import requests
import hashlib
from ecdsa import SigningKey
from ecdsa.util import sigencode_der, sigdecode_der
from dotenv import load_dotenv

load_dotenv()

HOST_NAME = os.getenv("BX_API_HOSTNAME")
JWT_TOKEN = os.getenv("BX_JWT")
AUTHORIZER = os.getenv("BX_AUTHORIZER")

public_key_pem = """
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE3on42czkgbLfobhZnHOw2cvRLPw+
ouotZAdvUO+BOc0yN9OS5aTplV2By9LT1+SuETeG4zLg7DytS4ct21ZZkA==
-----END PUBLIC KEY-----
"""

private_key_pem = """
-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgoE/ut6zgIQ2WBenX
scngA998+4fOr9ISC8DCrHqH342hRANCAATeifjZzOSBst+huFmcc7DZy9Es/D6i
6i1kB29Q74E5zTI305LlpOmVXYHL0tPX5K4RN4bjMuDsPK1Lhy3bVlmQ
-----END PRIVATE KEY-----
"""

# Decode the PEM-encoded private key
private_key = SigningKey.from_pem(private_key_pem)

session = requests.Session()
response = session.get(HOST_NAME + "/trading-api/v1/nonce", verify=False)
nonce = json.loads(response.text)["lowerBound"]
next_nonce = str(nonce + 1)
timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))

body = {
    "timestamp": timestamp,
    "nonce": next_nonce,
    "authorizer": AUTHORIZER,
    "command": {
        "commandType": "V1CreateOrder",
        "handle": None,
        "symbol": "BTCUSD",
        "type": "LMT",
        "side": "BUY",
        "price": "30071.5000",
        "stopPrice": None,
        "quantity": "1.87000000",
        "timeInForce": "GTC",
        "allowMargin": False,
    },
}

payload = (timestamp + next_nonce + "POST" + "/trading-api/v1/orders" + json.dumps(body, separators=(",", ":"))).encode("utf-8")
signature = private_key.sign(payload, hashfunc=hashlib.sha256, sigencode=sigencode_der)
signature = base64.b64encode(signature).decode()

headers = {
    "Content-type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}",
    "BX-SIGNATURE": signature,
    "BX-TIMESTAMP": timestamp,
    "BX-NONCE": next_nonce,
}

response = session.post(
    HOST_NAME + "/trading-api/v1/orders", json=body, headers=headers
)
print(f"HTTP Status: {response.status_code}, \n{response.text}")
