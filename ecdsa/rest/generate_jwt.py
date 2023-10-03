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
ENCODED_METADATA = os.getenv("BX_API_METADATA")

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
metadata = base64.b64decode(ENCODED_METADATA)
user_id = str(json.loads(metadata)["userId"])

timestamp = int(datetime.now(timezone.utc).timestamp())
expiration_time = int(timestamp + 300)
login_payload = {
    "userId": user_id,
    "nonce": timestamp,
    "expirationTime": expiration_time,
    "biometricsUsed": False,
    "sessionKey": None,
}

payload = (json.dumps(login_payload, separators=(",", ":"))).encode("utf-8")
signature = private_key.sign(payload, hashfunc=hashlib.sha256, sigencode=sigencode_der)
signature_base64 = base64.b64encode(signature).decode()

headers = {
    "Content-type": "application/json",
}
body = {
    "publicKey": public_key_pem[1:-1],
    "signature": signature_base64,
    "loginPayload": login_payload,
}

response = session.post(
    HOST_NAME + "/trading-api/v2/users/login",
    json=body,
    headers=headers,
    verify=False
)
print(f"HTTP Status: {response.status_code}, \n{response.text}")
