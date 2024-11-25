
Bullish API Examples
===================

This repository contains code examples to help developers get started with using the [Bullish cryptocurrency exchange](https://exchange.bullish.com/), via a programmatic interface.

Examples are based on the Bullish API documentation at https://api.exchange.bullish.com/docs/api/rest/#overview 

Getting started
-------

As with most of this code repository, code snippets below are written in Python 3. Some Java examples for [order creation](orders/java-examples/) and [withdrawal](custody/java-examples/) are also included.

## Connecting to the Bullish API
For functionality offered via the [Bullish API](https://api.exchange.bullish.com/docs/api/rest/#overview) - some can be accessed publicly (without prior login), and some are private, where a login session is required.

### Example public API - getting supported Markets

```python
import requests
import pprint

session = requests.Session()

headers = {
    "Content-type": "application/json"
}
response = session.get(
    "https://api.exchange.bullish.com/trading-api/v1/markets",
    headers=headers,
)
print(f"Response HTTP Status: {response.status_code}")
markets = response.json()
pprint.pp(markets) #pretty print
```

### Prerequisite to using private APIs - the JWT token
Important details about [how to start sending authenticated requests here](https://api.exchange.bullish.com/docs/api/rest/trading-api/v2/#overview--how-to-send-authenticated-requests). Some sample code on how to actually generate a JWT token:
- ECDSA example: [generate_jwt_v2.py](session/generate_jwt_ecdsa.py)
- HMAC example: [generate_jwt_hmac.py](session/generate_jwt_hmac.py)

### Example private API call - getting trading account ID(s)
Once you fetched your JWT Token successfully, you can fetch your trading account IDs via an authenticated request. For example:
```python
JWT_TOKEN = #Your JWT Token here
headers = {
    "Content-type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}",
}
response = session.get(
    "https://api.exchange.bullish.com/trading-api/v1/accounts/trading-accounts",
    headers=headers,
)
print(f"Response HTTP Status: {response.status_code}")
accounts = response.json()
pprint.pp(accounts)
```

### Signature required - creating a limit order
Signing of requests is done differently for HMAC and ECDSA. An [ECDSA example can be found here](orders/create_order_ecdsa.py), and a code snippet for HMAC is below. A [functional HMAC example can be found here](orders/create_order_hmac.py).
```python
JWT_TOKEN = #Your JWT Token here
TRADING_ACCOUNT_ID = # Your trading account id here
SECRET_KEY = # Your HMAC secret key here

timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))
next_nonce = str(int(datetime.now(timezone.utc).timestamp() * 1_000_000))

body = {
    "symbol": "ETHUSDC",
    "commandType": "V3CreateOrder",
    "type": "LIMIT",
    "side": "BUY",
    "quantity": "0.123",
    "price": "123.4", # A low price here, to make an example
    "timeInForce": "GTC",
    "allowBorrow": False,
    "clientOrderId": next_nonce,
    "tradingAccountId": TRADING_ACCOUNT_ID,
}
uri_path = "https://api.exchange.bullish.com/trading-api/v2/orders"
body_string = json.dumps(body, separators=(",", ":"))
payload = timestamp + next_nonce + "POST" + uri_path + body_string
digest = sha256(payload.encode("utf-8")).hexdigest().encode('utf-8')
signature = hmac.new(SECRET_KEY, digest, sha256).hexdigest()

headers = {
    "Content-type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}",
    "BX-SIGNATURE": signature,
    "BX-TIMESTAMP": timestamp,
    "BX-NONCE": next_nonce
}

response = session.post(
    uri_path, data=body_string, headers=headers
)

print(f"Response HTTP Status: {response.status_code}")
create_order_response = response.json()
pprint.pp(create_order_response)
```

Trying out the Python example code
-------
There are module dependencies that the code samples depend on. It is recommended the setup is done in a Python virtual environment, which can be initialised with:
```bash
python3 -m venv .
source ./bin/activate
```
Following which, we install the dependencies in [requirements.txt](requirements.txt)
```bash
pip3 install -r requirements.txt
```
In order to actually run the samples that involve calling private APIs, __credentials such as API keys and secrets need to be provided__. Our samples read these from the [.env file](.env) which looks like:
````
export BX_API_HOSTNAME=https://api.exchange.bullish.com
export BX_WS_API_HOSTNAME=wss://api.exchange.bullish.com

export BX_PUBLIC_KEY=< your credential >
export BX_PRIVATE_KEY=< your credential >
export BX_API_METADATA=< your credential >
export BX_TRADING_ACCOUNT_ID=< your credential >
````

Next steps
-----
Explore other functionality of the [Bullish API](https://api.exchange.bullish.com/docs/api/rest/#overview) via sample code, for example:
- Web socket for [Order Books](websocket/multi_orderbook_web_socket.py) 