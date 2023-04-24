import json
import os

import requests


HOST_NAME = os.getenv("BX_API_HOSTNAME")
JWT_TOKEN = os.getenv("BX_JWT")


session = requests.Session()


headers = {
    "Content-type": "application/json",
    "COOKIE": f"JWT_COOKIE={JWT_TOKEN}",
}

response = session.get(
    HOST_NAME + "/trading-api/v1/accounts/trading-accounts",
    headers=headers,
)
print(f"HTTP Status: {response.status_code}, \n{response.text}")
