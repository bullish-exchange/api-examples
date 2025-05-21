import json
import logging
import os
import requests
import sys
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s | %(levelname)-4s | %(threadName)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.StreamHandler(sys.stdout)])

HOST_NAME = os.getenv("BX_API_HOSTNAME")
JWT_TOKEN = os.getenv("BX_JWT")
TRADING_ACCOUNT_ID = os.getenv("BX_TRADING_ACCOUNT_ID")
PATH = "/trading-api/v2/otc-trades" + "?tradingAccountId=" + TRADING_ACCOUNT_ID

session = requests.Session()

headers = {
    "Content-type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}"
}

logging.info(f"headers=\n{json.dumps(headers, indent=2)}")

url = HOST_NAME + PATH
logging.info(f"URL: {url}")
response = session.get(
    url, 
    headers=headers,
    verify=False)

formatted_response = json.dumps(json.loads(response.text), indent=2)
logging.info(f"http_status={response.status_code} body=\n{formatted_response}")
