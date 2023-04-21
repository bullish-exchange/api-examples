
Python 3 Trading Scripts
--------
--------

This repository contains Python 3 API trading scripts for [Bullish](https://exchange.bullish.com/) cryptocurrency 
exchange. This set of scripts can be used out of the box. API traders can use these scripts as a starting point.

Bullish Trading API documentation: https://api.exchange.bullish.com/docs/api/rest/#overview 

## Install dependencies

```
pip3 install -r requirements.txt
```
## Prepare environment variables

Inside the `.env` file, override the default variables with your [JWT token](https://api.exchange.bullish.com/docs/api/rest/#overview--generate-a-jwt-token) 
and [API key](https://api.exchange.bullish.com/docs/api/rest/#overview--generate-an-api-key):
````
export BX_JWT=< your credential >

export BX_PUBLIC_KEY=< your credential >
export BX_PRIVATE_KEY=< your credential >
export BX_API_METADATA=< your credential >
export BX_AUTHORIZER=< your credential >
export BX_TRADING_ACCOUNT_ID=< your credential >
````

## Scripts

For a full walk-through on the usage of these scripts, start [here](https://api.exchange.bullish.com/docs/api/rest/#overview--how-to-send-authenticated-requests).  

- Generate a JWT token
- Create an order
- Cancel an order
- Read orders
