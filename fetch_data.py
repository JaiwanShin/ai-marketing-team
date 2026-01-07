"""
실제 네이버 API를 사용한 카밍패드 마케팅 분석
"""
import os
import json
from dotenv import load_dotenv
import time
import hmac
import hashlib
import base64
import requests

load_dotenv()

# Search Ad API
AD_API_KEY = os.getenv("NAVER_SEARCH_AD_API_KEY")
AD_SECRET_KEY = os.getenv("NAVER_SEARCH_AD_SECRET_KEY")
CUSTOMER_ID = os.getenv("NAVER_CUSTOMER_ID")
AD_BASE_URL = "https://api.naver.com"

# Shopping API
CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")


def get_ad_header(method, uri):
    timestamp = str(int(time.time() * 1000))
    signature = hmac.new(
        AD_SECRET_KEY.encode(),
        f"{timestamp}.{method}.{uri}".encode(),
        hashlib.sha256
    ).digest()
    
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": AD_API_KEY,
        "X-Customer": str(CUSTOMER_ID),
        "X-Signature": base64.b64encode(signature).decode()
    }


def get_keywords(hint_keyword):
    """검색광고 API - 연관 키워드 조회"""
    uri = "/keywordstool"
    headers = get_ad_header("GET", uri)
    params = {"hintKeywords": hint_keyword, "showDetail": "1"}
    
    response = requests.get(f"{AD_BASE_URL}{uri}", headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Keyword API Error: {response.status_code}")
        return None


def search_shopping(query, display=100):
    """쇼핑 API - 상품 검색"""
    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    params = {"query": query, "display": display, "sort": "sim"}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Shopping API Error: {response.status_code}")
        return None


print("=" * 60)
print("🎯 캄프 카밍패드 마케팅 분석 시작")
print("=" * 60)

# 1. 키워드 분석
print("\n📊 [1/3] 키워드 데이터 수집 중...")
keyword_data = get_keywords("카밍패드")

if keyword_data and "keywordList" in keyword_data:
    keywords = keyword_data["keywordList"]
    print(f"   ✓ {len(keywords)}개 키워드 수집 완료")
    
    # 상위 20개 키워드 저장
    top_keywords = sorted(keywords, key=lambda x: (x.get("monthlyPcQcCnt", 0) or 0) + (x.get("monthlyMobileQcCnt", 0) or 0), reverse=True)[:20]
    
    with open("outputs/keyword_api_data.json", "w", encoding="utf-8") as f:
        json.dump(top_keywords, f, ensure_ascii=False, indent=2)
    print("   ✓ outputs/keyword_api_data.json 저장 완료")
else:
    print("   ✗ 키워드 데이터 수집 실패")
    top_keywords = []

# 2. 쇼핑 데이터 (가격)
print("\n💰 [2/3] 쇼핑 데이터 수집 중...")
shopping_data = search_shopping("카밍패드", 100)

if shopping_data and "items" in shopping_data:
    items = shopping_data["items"]
    print(f"   ✓ {len(items)}개 상품 수집 완료")
    
    # 가격 분석
    prices = [int(item["lprice"]) for item in items if item.get("lprice")]
    prices.sort()
    
    if prices:
        price_stats = {
            "min": prices[0],
            "q1": prices[len(prices)//4],
            "median": prices[len(prices)//2],
            "q3": prices[3*len(prices)//4],
            "max": prices[-1],
            "count": len(prices)
        }
        
        with open("outputs/price_api_data.json", "w", encoding="utf-8") as f:
            json.dump({"stats": price_stats, "sample_items": items[:20]}, f, ensure_ascii=False, indent=2)
        print("   ✓ outputs/price_api_data.json 저장 완료")
else:
    print("   ✗ 쇼핑 데이터 수집 실패")
    price_stats = None
    items = []

# 3. 결과 요약 출력
print("\n" + "=" * 60)
print("📋 수집 결과 요약")
print("=" * 60)

if top_keywords:
    print("\n🔑 TOP 5 키워드:")
    for i, kw in enumerate(top_keywords[:5], 1):
        pc = kw.get("monthlyPcQcCnt", 0) or 0
        mobile = kw.get("monthlyMobileQcCnt", 0) or 0
        total = pc + mobile
        comp = kw.get("compIdx", "N/A")
        print(f"   {i}. {kw['relKeyword']} - 월검색량: {total:,} (경쟁: {comp})")

if price_stats:
    print(f"\n💰 가격 분포:")
    print(f"   최저가: {price_stats['min']:,}원")
    print(f"   중앙값: {price_stats['median']:,}원")
    print(f"   최고가: {price_stats['max']:,}원")

print("\n✅ 데이터 수집 완료!")
print("   다음 단계: 에이전트 분석 실행")
