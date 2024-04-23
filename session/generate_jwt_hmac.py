import hmac, requests, os
from datetime import datetime, timezone
from dotenv import load_dotenv
from hashlib import sha256

load_dotenv()

HOST_NAME = os.getenv("BX_API_HOSTNAME")
PUBLIC_KEY = os.getenv("BX_PUBLIC_KEY")
SECRET_KEY = bytes(os.getenv("BX_SECRET_KEY"), 'utf-8')

session = requests.Session()
nonce = int(datetime.now(timezone.utc).timestamp())
ts = str(int(datetime.now(timezone.utc).timestamp() * 1000))
path = "/trading-api/v1/users/hmac/login"
message = ts + nonce + "GET" + "/trading-api/v1/users/hmac/login"
signature = hmac.new(SECRET_KEY, message.encode("utf-8"), sha256).hexdigest()

headers = {
    'BX-PUBLIC-KEY': PUBLIC_KEY,
    'BX-NONCE': nonce,
    'BX-SIGNATURE': signature,
    'BX-TIMESTAMP': ts
}
url = HOST_NAME + path
response = session.get(url, headers=headers)

print(f"HTTP Status: {response.status_code}, \n{response.text}")