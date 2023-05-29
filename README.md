
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

Scripts in this repository rely on environment variables.

Those have to be supplied via an `.env` file in the below format. [Here](.env)

````
export BX_JWT=< your credential >
export BX_PUBLIC_KEY=< your credential >
export BX_PRIVATE_KEY=< your credential >
export BX_API_METADATA=< your credential >
export BX_AUTHORIZER=< your credential >
export BX_TRADING_ACCOUNT_ID=< your credential >
````

More info on how to obtain them is available in [this guide](https://api.exchange.bullish.com/docs/api/rest/#overview--how-to-send-authenticated-requests).  

Specifically,

- [API key (Public Key, Private Key, API Metadata)](https://api.exchange.bullish.com/docs/api/rest/#overview--generate-an-api-key):

- [Login Tokens (JWT token and Authorizer)](https://api.exchange.bullish.com/docs/api/rest/#overview--generate-a-jwt-token) 

- Trading Account Ids

