# 네이버 쇼핑 API 사용 가이드

## API 개요
네이버 쇼핑 API를 통해 상품 정보, 가격, 리뷰 데이터를 수집합니다.

## 인증 정보
```python
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
BASE_URL = "https://openapi.naver.com/v1/search/shop.json"
```

## 주요 엔드포인트

### 1. 상품 검색
```
GET /v1/search/shop.json
```
- 입력: 검색어, 정렬, 개수
- 출력: 상품명, 가격, 판매처, 링크, 이미지

## 사용 예시
```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
BASE_URL = "https://openapi.naver.com/v1/search/shop.json"

def search_products(query: str, display: int = 100, sort: str = "sim") -> dict:
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    params = {
        "query": query,
        "display": display,
        "sort": sort
    }
    response = requests.get(BASE_URL, headers=headers, params=params)
    return response.json()

def get_price_stats(products: list) -> dict:
    """가격 통계 계산"""
    prices = [int(p["lprice"]) for p in products if p.get("lprice")]
    prices.sort()
    
    n = len(prices)
    return {
        "min": prices[0],
        "q1": prices[n // 4],
        "median": prices[n // 2],
        "q3": prices[3 * n // 4],
        "max": prices[-1],
        "count": n
    }
```

## 응답 데이터 구조
```json
{
  "total": 12345,
  "items": [
    {
      "title": "<b>에어팟</b> <b>맥스</b> 실버",
      "link": "https://...",
      "image": "https://...",
      "lprice": "669000",
      "hprice": "750000",
      "mallName": "쿠팡",
      "productId": "12345678",
      "productType": "1",
      "brand": "Apple",
      "maker": "Apple",
      "category1": "디지털/가전",
      "category2": "음향기기",
      "category3": "헤드폰",
      "category4": "무선헤드폰"
    }
  ]
}
```

## 데이터 정제
```python
import re

def clean_title(title: str) -> str:
    """HTML 태그 제거"""
    return re.sub(r"<[^>]+>", "", title)

def categorize_by_price(products: list) -> dict:
    """가격대별 분류"""
    stats = get_price_stats(products)
    
    low = [p for p in products if int(p["lprice"]) < stats["q1"]]
    mid = [p for p in products if stats["q1"] <= int(p["lprice"]) < stats["q3"]]
    high = [p for p in products if int(p["lprice"]) >= stats["q3"]]
    
    return {"low": low, "mid": mid, "high": high}
```

## 주의사항
- 일일 호출 제한: 25,000회
- 한 번에 최대 100개 결과
- 상업적 이용 시 별도 계약 필요
