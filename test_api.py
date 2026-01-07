import os
from dotenv import load_dotenv
import time
import hmac
import hashlib
import base64
import requests

load_dotenv()

API_KEY = os.getenv("NAVER_SEARCH_AD_API_KEY")
SECRET_KEY = os.getenv("NAVER_SEARCH_AD_SECRET_KEY")
CUSTOMER_ID = os.getenv("NAVER_CUSTOMER_ID")
BASE_URL = "https://api.naver.com"

def get_header(method, uri, api_key, secret_key, customer_id):
    timestamp = str(int(time.time() * 1000))
    signature = hmac.new(
        secret_key.encode(),
        f"{timestamp}.{method}.{uri}".encode(),
        hashlib.sha256
    ).digest()
    
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": api_key,
        "X-Customer": str(customer_id),
        "X-Signature": base64.b64encode(signature).decode()
    }

print("Testing Naver Search Ad API...")
uri = "/keywordstool"
headers = get_header("GET", uri, API_KEY, SECRET_KEY, CUSTOMER_ID)
params = {"hintKeywords": "카밍패드", "showDetail": "1"}
response = requests.get(f"{BASE_URL}{uri}", headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    print(f"✅ Success! Found {len(data['keywordList'])} keywords.")
    print(f"Top keyword: {data['keywordList'][0]['relKeyword']}")
else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text)
