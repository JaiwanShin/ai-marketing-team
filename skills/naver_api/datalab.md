# 네이버 데이터랩 API 사용 가이드

## API 개요
네이버 데이터랩 API를 통해 검색어 트렌드 데이터를 수집합니다.

## 인증 정보
```python
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
BASE_URL = "https://openapi.naver.com/v1/datalab/search"
```

## 주요 엔드포인트

### 1. 검색어 트렌드
```
POST /v1/datalab/search
```
- 입력: 키워드 그룹, 기간, 시간 단위
- 출력: 상대적 검색량 (0-100)

## 사용 예시
```python
import requests
from datetime import datetime, timedelta

def get_search_trend(
    keywords: list[str],
    start_date: str = None,
    end_date: str = None,
    time_unit: str = "week"
) -> dict:
    """
    검색어 트렌드 조회
    
    Args:
        keywords: 키워드 목록
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        time_unit: 시간 단위 (date, week, month)
    
    Returns:
        트렌드 데이터
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
        "Content-Type": "application/json"
    }
    
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": [
            {"groupName": kw, "keywords": [kw]} for kw in keywords
        ]
    }
    
    response = requests.post(BASE_URL, headers=headers, json=body)
    return response.json()

def calculate_trend_change(data: dict) -> dict:
    """트렌드 변화율 계산"""
    results = {}
    
    for group in data.get("results", []):
        keyword = group["title"]
        values = [d["ratio"] for d in group["data"]]
        
        if len(values) >= 2:
            current = values[-1]
            previous = values[-2]
            change_pct = ((current - previous) / previous * 100) if previous > 0 else 0
            
            results[keyword] = {
                "current": current,
                "previous": previous,
                "change_pct": round(change_pct, 2),
                "trend": "📈 상승" if change_pct > 5 else "📉 하락" if change_pct < -5 else "➡️ 유지"
            }
    
    return results
```

## 응답 데이터 구조
```json
{
  "startDate": "2024-01-01",
  "endDate": "2024-12-31",
  "timeUnit": "month",
  "results": [
    {
      "title": "에어팟 맥스",
      "keywords": ["에어팟 맥스"],
      "data": [
        {"period": "2024-01-01", "ratio": 45.2},
        {"period": "2024-02-01", "ratio": 52.1},
        {"period": "2024-03-01", "ratio": 48.7}
      ]
    }
  ]
}
```

## 연령/성별 분석
```python
def get_demographic_trend(keyword: str) -> dict:
    """연령/성별별 트렌드 (쇼핑인사이트 API)"""
    url = "https://openapi.naver.com/v1/datalab/shopping/category/keyword/age"
    # ... 구현
    pass
```

## 주의사항
- 최대 5개 키워드 그룹
- 그룹당 최대 20개 키워드
- 최대 조회 기간: 지난 5년
- ratio 값은 상대적 수치 (최대값 100 기준)
