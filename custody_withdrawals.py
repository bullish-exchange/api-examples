"""
The sample code here demonstrates how to perform a withdrawal using the Bullish API

The calls here require an API key that has been created with 'Withdrawal' privileges and had the destination signed
on the Bullish website.

The script assumes you have setup your environment variables as descried in README.md including generating a JWT token

WARNING: The script here will perform a full withdrawal providing a correct API key and destination are used, please
be careful to avoid any accidental transactions.

Withdrawals consist of 3 basic actions:

    1) Get your destinationId
    2) Request a challenge for your withdrawal requirements
    3) Sign the challenge (assertion) to perform the withdrawal

Note: after getting your destinationId, the withdrawal process is identical for both fiat and crypto.
"""
import json
import os
from datetime import datetime, timezone
from hashlib import sha256

import requests
from eosio_signer import EOSIOKey

import secrets

HOST_NAME = os.getenv("BX_API_HOSTNAME")
PRIVATE_KEY = os.getenv("BX_PRIVATE_KEY")
PUBLIC_KEY = os.getenv("BX_PUBLIC_KEY")
JWT_TOKEN = os.getenv("BX_JWT")

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

    /trading-api/v1/wallets/withdrawal-instructions/crypto/BTC

    or

    /trading-api/v1/wallets/withdrawal-instructions/fiat/USD

Each of these responses contains a field named destinationId

{
    "destinationId": "2097b2374a02a345b23845c023d84c502d83cf45c23ed2345acb98b274",
    ...
}

"""
print("Step 1: Get destinationId from /trading-api/v1/wallets/withdrawal-instructions/fiat/USD", end="\n\n")

response = requests.Session().get(
  HOST_NAME + "/trading-api/v1/wallets/withdrawal-instructions/fiat/USD",
  headers = headers,
  verify = True
)

# We'll assume the first USD instruction is where we want the withdrawal to go
fiatDestinationId = response.json()[0]["destinationId"]
print(f"destinationId={fiatDestinationId}", end="\n\n")

"""
Step 2: Request a challenge for your withdrawal requirements

Submit the details of the withdrawal you wish to make and the Bullish API will return a challenge for signing

The nonce is used to protect against replay attacks, it is not meant as a universal idempotency key for all withdrawals,
change it for each withdrawal.withdrawal

For a crypto withdrawal, use exactly the same process, but use for example

    {
        network: "BTC",
        symbol: "BTC",
        ...
    }

    or

    {
        network: "ETH",
        symbol: "USDC",
        ...
    }

"""
print("Step 2: Request withdrawal challenge from /trading-api/v1/wallets/withdrawal-challenge", end="\n\n")

withdrawBody = {
    "nonce" : str(secrets.randbelow( 2**63-1)),
    "command" : {
        "commandType": "V1WithdrawalChallenge",
        "destinationId": fiatDestinationId,
        "network": "SEN",
        "symbol": "USD",
        "quantity": "10"
    }
}

withdrawChallengeResponse = requests.Session().post(
    HOST_NAME + "/trading-api/v1/wallets/withdrawal-challenge",
    headers = headers,
    json = withdrawBody,
    verify = True
)

withdrawalJson = withdrawChallengeResponse.json()
challenge = withdrawalJson['challenge']
print( f"challenge={challenge}", end="\n\n")

"""
Step 3: Sign the challenge (assertion) to perform the withdrawal

Sign the challenge from Step 2 with your private key, and send this back to Bullish to initiate the withdrawal
"""
print("Step 3: Submit signed challenge to perform withdrawal to /trading-api/v1/wallets/withdrawal-assertion", end="\n\n")

eos_key = EOSIOKey(PRIVATE_KEY)
signature = eos_key.sign(challenge)

print( f"signature={signature}", end="\n\n")

withdrawAssertion = {
    "command" : {
        "commandType" : "V1WithdrawalAssertion",
        "signature": signature,
        "challenge": challenge,
        "publicKey": PUBLIC_KEY
    }
}

withdrawAssertionResponse = requests.Session().post(
    HOST_NAME + "/trading-api/v1/wallets/withdrawal-assertion",
    headers = headers,
    json = withdrawAssertion,
    verify = True
)

withdrawalAssertionResponseJson = withdrawAssertionResponse.json()
print( f"JSON Response to Withdrawal Assertion={withdrawalAssertionResponseJson}", end="\n\n")