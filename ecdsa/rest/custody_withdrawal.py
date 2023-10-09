import base64
import json
import os
import time
import uuid
from hashlib import sha256
import requests
import hashlib
from ecdsa import SigningKey
from ecdsa.util import sigencode_der, sigdecode_der
from dotenv import load_dotenv

load_dotenv()

HOST_NAME = os.getenv("BX_API_HOSTNAME")
AUTHORIZER = os.getenv("BX_AUTHORIZER")
JWT_TOKEN = os.getenv("BX_JWT")

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

"""
session and headers are consistent for all calls in this file
"""
session = requests.Session()
headers = {
  "Content-type": "application/json",
  "Authorization" : "Bearer " + JWT_TOKEN
}

"""
Step 1: Get your signed destinationId

Note: destinations must be signed on the Bullish website, this cannot be done through the API

This is simply a matter of calling either the crypto or fiat endpoint:

    /trading-api/v1/wallets/withdrawal-instructions/crypto/EOS

    or

    /trading-api/v1/wallets/withdrawal-instructions/fiat/USD

Each of these responses contains a field named destinationId

{
    "destinationId": "2097b2374a02a345b23845c023d84c502d83cf45c23ed2345acb98b274",
    ...
}

"""
print("Step 1: Get destinationId from /trading-api/v1/wallets/withdrawal-instructions/crypto/EOS", end="\n\n")

response = session.get(
  HOST_NAME + "/trading-api/v1/wallets/withdrawal-instructions/crypto/EOS",
  headers = headers,
  verify = True
)

# We'll assume the first EOS instruction is where we want the withdrawal to go
destination_id = response.json()[0]["destinationId"]
print(f"destinationId={destination_id}", end="\n\n")

"""
Step 2: Create an ECDSA signature for your withdrawal request

Create a string by concatenating timestamp, nonce, http method, endpoint and body

The nonce is used to protect against replay attacks, it is not meant as a universal idempotency key for all withdrawals,
change it for each withdrawal.

Using the following EOS withdrawal request as an example.

    {
        nonce: "85548fae-5fec-44ab-83a4-c6bf2d4c8788",
        timestamp: "1696841072969",
        ...
        "command": {
            ...
            "network": "EOS",
            "symbol": "EOS",
            "quantity": "0.1"
        }
    }

Create a string for signing by joining the nonce, current epoch time in milliseconds, the withdrawal endpoint and the request

body in JSON.

    169684107296985548fae-5fec-44ab-83a4-c6bf2d4c8788/trading-api/v1/wallets/withdrawal{"nonce":"85548fae-5fec-44ab-83a4-c6bf2d4c8788",...}


Then sign it with the ECDSA private key, apply BASE64 encoding, and pass it in the headers as BX-SIGNATURE.

"""

# Create withdrawal request body
timestamp = str(time.time_ns() // 1_000_000)
nonce = str(uuid.uuid4())
withdraw_payload = {
    "nonce" : nonce,
    "timestamp": timestamp,
    "authorizer": AUTHORIZER,
    "command" : {
        "commandType": "V1Withdrawal",
        "destinationId": destination_id,
        "network": "EOS",
        "symbol": "EOS",
        "quantity": "0.1"
    }
}

# Create string for signing
withdraw_payload_str = str((json.dumps(withdraw_payload, separators=(",", ":"))).encode("utf-8"), 'utf-8')
signature_payload=f"""{timestamp}{nonce}POST/trading-api/v1/wallets/withdrawal{withdraw_payload_str}"""
signature_payload_bytes = bytes(signature_payload, 'utf-8')

# Decode the PEM-encoded private key
private_key = SigningKey.from_pem(private_key_pem)

# Sign string with private key and encode it with BASE64
signature = private_key.sign(signature_payload_bytes, hashfunc=hashlib.sha256, sigencode=sigencode_der)
signature_base64 = base64.b64encode(signature).decode()

headers["BX-SIGNATURE"] = signature_base64

withdraw_response = session.post(
    HOST_NAME + "/trading-api/v1/wallets/withdrawal",
    headers = headers,
    json=withdraw_payload,
    verify=True
)

print(f"Withdrawal HTTP Status: {withdraw_response.status_code}")

withdraw_response_json = withdraw_response.json()
print(f"JSON Response to Withdrawal Request: {withdraw_response_json}")