# 네이버 검색광고 API 사용 가이드

## API 개요
네이버 검색광고 API를 통해 키워드의 검색량, 클릭수, 경쟁 강도 등을 조회합니다.


## 사용 예시
```python
import os
import time
import hmac
import hashlib
import base64
import requests
from dotenv import load_dotenv

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

def get_related_keywords(keyword: str) -> dict:
    """연관 키워드 조회"""
    uri = "/keywordstool"
    headers = get_header("GET", uri, API_KEY, SECRET_KEY, CUSTOMER_ID)
    params = {
        "hintKeywords": keyword,
        "showDetail": "1"
    }
    
    response = requests.get(f"{BASE_URL}{uri}", headers=headers, params=params)
    if response.status_code != 200:
        return {"error": response.text}
        
    return response.json()
```


## 응답 데이터 구조
```json
{
  "keywordList": [
    {
      "relKeyword": "에어팟 맥스",
      "monthlyPcQcCnt": 12000,
      "monthlyMobileQcCnt": 45000,
      "monthlyAvePcClkCnt": 800,
      "monthlyAveMobileClkCnt": 3200,
      "compIdx": "높음",
      "plAvgDepth": 15
    }
  ]
}
```

## 주의사항
- API 호출 제한: 분당 1000회
- 인증 정보는 환경변수로 관리 권장
