"""
The examples here demonstrate simple usage of the GET endpoints of Bullish Custody API offering

This script only makes read only requests and can be safely run in it's entirety. It also assumes you have setup your
environment variables as descried in README.md including generating a JWT token
"""
import json
import os
from datetime import datetime, timezone
from hashlib import sha256

import requests
from eosio_signer import EOSIOKey

HOST_NAME = os.getenv("BX_API_HOSTNAME")
PRIVATE_KEY = os.getenv("BX_PRIVATE_KEY")
JWT_TOKEN = os.getenv("BX_JWT")

session = requests.Session()
headers = {
  "Content-type": "application/json",
  "Authorization" : "Bearer " + JWT_TOKEN
}

"""
Transaction History
"""
print( "/trading-api/v1/wallets/transactions", end="\n\n")

transactionsResponse = requests.Session().get(
  HOST_NAME + "/trading-api/v1/wallets/transactions",
  headers = headers,
  verify=True
)

print(transactionsResponse.json(), end="\n\n\n")

"""
Deposit Instructions for crypto and fiat
"""
print("/trading-api/v1/wallets/deposit-instructions/crypto/BTC", end="\n\n")

response = requests.Session().get(
  HOST_NAME + "/trading-api/v1/wallets/deposit-instructions/crypto/BTC",
  headers = headers,
  verify=True
)

print(response.json(), end="\n\n\n")

print("/trading-api/v1/wallets/deposit-instructions/fiat/USD", end="\n\n")

response = requests.Session().get(
  HOST_NAME + "/trading-api/v1/wallets/deposit-instructions/fiat/USD",
  headers = headers,
  verify=True
)

print(response.json(), end="\n\n\n")

"""
Withdrawal Instructions for crypto and fiat
"""
print("/trading-api/v1/wallets/withdrawal-instructions/crypto/BTC", end="\n\n")

response = requests.Session().get(
  HOST_NAME + "/trading-api/v1/wallets/withdrawal-instructions/crypto/BTC",
  headers = headers,
  verify=True
)

print(response.json(), end="\n\n\n")

print("/trading-api/v1/wallets/withdrawal-instructions/fiat/USD", end="\n\n")

response = requests.Session().get(
  HOST_NAME + "/trading-api/v1/wallets/withdrawal-instructions/fiat/USD",
  headers = headers,
  verify=True
)

print(response.json(), end="\n\n\n")

"""
Limits for crypto and fiat
"""
print("/trading-api/v1/wallets/limits/BTC", end="\n\n")

response = requests.Session().get(
  HOST_NAME + "/trading-api/v1/wallets/limits/BTC",
  headers = headers,
  verify=True
)

print(response.json(), end="\n\n\n")

print("/trading-api/v1/wallets/limits/USD", end="\n\n")

response = requests.Session().get(
  HOST_NAME + "/trading-api/v1/wallets/limits/USD",
  headers = headers,
  verify=True
)

print(response.json(), end="\n\n\n")