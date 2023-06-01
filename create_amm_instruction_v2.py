import json
import math
import os
from datetime import datetime, timezone
from hashlib import sha256
import requests
from eosio_signer import EOSIOKey
from dotenv import load_dotenv

load_dotenv()

HOST_NAME = os.getenv("BX_API_HOSTNAME")
PRIVATE_KEY = os.getenv("BX_PRIVATE_KEY")
JWT_TOKEN = os.getenv("BX_JWT")
AUTHORIZER = os.getenv("BX_AUTHORIZER")
TRADING_ACCOUNT_ID = os.getenv("BX_TRADING_ACCOUNT_ID")

session = requests.Session()
response = session.get(HOST_NAME + "/trading-api/v1/nonce", verify=False)
nonce = json.loads(response.text)["lowerBound"]
next_nonce = str(nonce + 1)
timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))

SYMBOL = "BTCUSD"
FEE_TIER = "1"
PRICE_LOWER_BOUND = "70000.0000"
PRICE_UPPER_BOUND = "80000.0000"


def get_market_by_symbol(symbol):
    return session.get(HOST_NAME + f"/trading-api/v1/markets/{symbol}").json()


def get_current_amm_price(fee_tier, symbol):
    response_body = session.get(HOST_NAME + f"/trading-api/v1/markets/{symbol}/tick").json()
    amm_list = response_body["ammData"]
    for amm in amm_list:
        if amm["feeTierId"] is fee_tier:
            return amm["currentPrice"]
    raise Exception("Invalid fee tier")


def get_adjustment_factor(current_price, price_lower, price_upper):
    sqrt_p = math.sqrt(float(current_price))
    sqrt_p_l = math.sqrt(float(price_lower))
    sqrt_p_u = math.sqrt(float(price_upper))
    return (sqrt_p * sqrt_p_u * (sqrt_p - sqrt_p_l)) / (sqrt_p_u - sqrt_p)


def get_adjusted_base_amount(quote_amount, current_price, price_lower, price_upper):
    base_precision = get_market_by_symbol(SYMBOL)["basePrecision"]
    factor = get_adjustment_factor(current_price, price_lower, price_upper)
    if price_lower > price_upper or current_price >= price_upper:
        base = 0
    else:
        base = float(quote_amount) / factor
    return "{:.{}f}".format(abs(base), base_precision)


def get_adjusted_quote_amount(base_amount, current_price, price_lower, price_upper):
    quote_precision = get_market_by_symbol(SYMBOL)["quotePrecision"]
    factor = get_adjustment_factor(current_price, price_lower, price_upper)
    if price_lower > price_upper or current_price <= price_lower:
        quote = 0
    else:
        quote = float(base_amount) * factor
    return "{:.{}f}".format(abs(quote), quote_precision)


body = {
    "timestamp": timestamp,
    "nonce": next_nonce,
    "authorizer": AUTHORIZER,
    "command": {
        "commandType": "V2AddLiquidity",
        "symbol": SYMBOL,
        "baseQuantity": "1.00000000",
        "quoteQuantity": get_adjusted_quote_amount("1.00000000", get_current_amm_price(FEE_TIER, SYMBOL),
                                                   PRICE_LOWER_BOUND, PRICE_UPPER_BOUND),
        "upperBound": PRICE_UPPER_BOUND,
        "lowerBound": PRICE_LOWER_BOUND,
        "feeTierId": FEE_TIER,
        "tradingAccountId": TRADING_ACCOUNT_ID,
    },
}

payload = (json.dumps(body, separators=(",", ":"))).encode("utf-8")
digest = sha256(payload.rstrip()).hexdigest()
eos_key = EOSIOKey(PRIVATE_KEY)
signature = eos_key.sign(digest)

headers = {
    "Content-type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}",
    "BX-SIGNATURE": signature,
    "BX-TIMESTAMP": timestamp,
    "BX-NONCE": next_nonce,
}

response = session.post(
    HOST_NAME + "/trading-api/v1/amm-instructions", json=body, headers=headers
)
print(f"HTTP Status: {response.status_code}, \n{response.text}")
