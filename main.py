"""
main.py - Data Marketing Agent Team Orchestrator

에이전트 팀을 조합하고 실행합니다.
백그라운드 스레드에서 실행되어 대시보드와 동시에 작동합니다.
"""

import os
import time
import threading
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# OpenAI 또는 다른 LLM 클라이언트
# from openai import OpenAI

from config import load_all_agents, load_skill, build_system_prompt, AgentConfig
from logger import logger, LogLevel
from fetch_data import get_keywords, search_shopping


class MarketingAgentTeam:
    """데이터 마케팅 에이전트 팀"""
    
    def __init__(self):
        self.agents = load_all_agents()
        self.skills = self._load_skills()
        
        print("🚀 Marketing Agent Team 초기화 완료")
        print(f"   - Orchestrator: {len(self.agents.get('orchestrator', []))}명")
        print(f"   - Data Team: {len(self.agents.get('data_team', []))}명")
        print(f"   - Content Team: {len(self.agents.get('content_team', []))}명")
    
    def _load_skills(self) -> dict[str, str]:
        """스킬 파일 로드"""
        skills = {}
        skills_dir = Path("skills/naver_api")
        
        if skills_dir.exists():
            for skill_file in skills_dir.glob("*.md"):
                skill_name = skill_file.stem
                skills[skill_name] = load_skill(str(skill_file))
        
        return skills
    
    def _get_agent(self, team: str, name: str) -> Optional[AgentConfig]:
        """에이전트 가져오기"""
        for agent in self.agents.get(team, []):
            if agent.name == name:
                return agent
        return None
    
    def _execute_agent_logic(self, agent: AgentConfig, task: str) -> str:
        """에이전트별 실제 로직 실행 (LLM 대체)"""
        
        # 1. Keyword Researcher
        if agent.name == "keyword_researcher":
            logger.log(agent.name, LogLevel.ACTION, "🔍 네이버 검색광고 API 호출 중...")
            data = get_keywords("카밍패드") # 데모용 고정 키워드
            if data and "keywordList" in data:
                keywords = data["keywordList"][:10]
                result = "### 🔑 키워드 분석 결과\n\n"
                for kw in keywords:
                    result += f"- **{kw['relKeyword']}**: 월간검색수 {kw['monthlyPcQcCnt'] + kw['monthlyMobileQcCnt']:,}\n"
                return result
            return "키워드 데이터를 가져오지 못했습니다."

        # 2. Price Monitor
        elif agent.name == "price_monitor":
            logger.log(agent.name, LogLevel.ACTION, "💰 네이버 쇼핑 API 호출 중...")
            data = search_shopping("카밍패드")
            if data and "items" in data:
                items = data["items"][:5]
                result = "### 💰 가격 모니터링 결과\n\n"
                prices = [int(item["lprice"]) for item in items]
                avg_price = sum(prices) / len(prices)
                result += f"**평균 가격**: {avg_price:,.0f}원\n\n"
                for item in items:
                    result += f"- [{item['title']}]({item['link']}) : **{int(item['lprice']):,}원**\n"
                return result
            return "쇼핑 데이터를 가져오지 못했습니다."
            
        # 3. Product Copywriter
        elif agent.name == "product_copywriter":
            time.sleep(2)
            return """
### ✨ 캄프 풋귤 카밍 패드 (개선안)

**상품명**: [진정/미백] 캄프 풋귤 비타 플루이드 카밍 패드 (70매)

**핵심 소구점**:
1. **제주 풋귤 추출물**: 비타민 C가 풍부하여 맑은 피부톤 케어
2. **나이아신아마이드**: 식약처 고시 미백 기능성 성분 함유
3. **플루이드 제형**: 끈적임 없이 산뜻한 흡수력

**상세 설명**:
지친 피부에 생기를 더하는 '제주 풋귤'의 에너지! 
일반 귤보다 비타민 C가 훨씬 풍부한 청귤(풋귤) 추출물을 듬뿍 담았습니다. 
나이아신아마이드 성분이 더해져 칙칙한 피부톤을 환하게 밝혀줍니다.
"""

        # 4. Reviewer
        elif agent.name == "reviewer":
            time.sleep(1)
            return """
### ✅ 품질 검수 완료

**검토 결과**: 승인 (Approved)
**수정 사항 반영**:
- 기존 '시카/센텔라' 키워드 제거 완료
- '제주 풋귤', '나이아신아마이드' 성분 강조 확인됨
- 키워드 및 가격 데이터 기반 분석 적절함

사용자 승인을 위해 최종 리포트를 생성합니다.
"""

        # Other Agents (Planner, etc.)
        else:
            time.sleep(2)
            return f"""
### {agent.name} 분석 결과

요청하신 작업에 대한 분석을 완료했습니다.
(이 에이전트는 현재 데모 모드로 작동 중입니다.)

**주요 내용**:
- 작업 목표 달성
- 데이터 분석 완료
- 다음 단계 진행 가능
"""
    
    def run_agent(self, team: str, agent_name: str, task: str) -> str:
        """단일 에이전트 실행"""
        agent = self._get_agent(team, agent_name)
        if not agent:
            raise ValueError(f"Agent not found: {team}/{agent_name}")
        
        logger.set_current_agent(agent_name, f"{agent_name} 작업 중...")
        logger.log(agent_name, LogLevel.THINKING, f"📋 작업 수신: {task[:50]}...")
        
        # LLM 대신 실행 로직 호출
        result = self._execute_agent_logic(agent, task)
        
        # 결과 저장
        output_path = logger.save_output(agent_name, result)
        logger.complete_agent(agent_name)
        
        return result
    
    def run_workflow(self, user_request: str):
        """
        전체 워크플로우 실행
        
        Planner -> Data Team -> Content Team -> Reviewer
        """
        logger.clear_logs()
        
        print(f"\n{'='*60}")
        print(f"📌 사용자 요청: {user_request}")
        print(f"{'='*60}\n")
        
        # 1. Planner
        logger.log("system", LogLevel.INFO, "🎯 워크플로우 시작")
        planner_result = self.run_agent("orchestrator", "planner", user_request)
        
        # 2. Data Team (순차 실행)
        logger.log("system", LogLevel.INFO, "📊 Data Team 순차 실행 시작")
        data_results = {}
        
        for agent in self.agents.get("data_team", []):
            task = f"다음 분석 요청에 대해 작업해주세요:\n\n원본 요청: {user_request}\n\nPlanner 지시사항: {planner_result}"
            data_results[agent.name] = self.run_agent("data_team", agent.name, task)
        
        logger.log("system", LogLevel.INFO, "📊 Data Team 완료")
        
        # 3. Content Team (순차 실행)
        logger.log("system", LogLevel.INFO, "✍️ Content Team 순차 실행 시작")
        content_results = {}
        combined_data = "\n\n---\n\n".join([f"## {k}\n{v}" for k, v in data_results.items()])
        
        for agent in self.agents.get("content_team", []):
            task = f"다음 분석 결과를 바탕으로 콘텐츠를 생성해주세요:\n\n{combined_data}"
            content_results[agent.name] = self.run_agent("content_team", agent.name, task)
        
        logger.log("system", LogLevel.INFO, "✍️ Content Team 완료")
        
        # 4. Reviewer
        all_results = {**data_results, **content_results}
        review_input = "\n\n---\n\n".join([f"## {k}\n{v}" for k, v in all_results.items()])
        reviewer_result = self.run_agent("orchestrator", "reviewer", f"다음 결과물들을 검토해주세요:\n\n{review_input}")
        
        # 최종 리포트 저장
        content_section = "".join([f"### {k}\n{v}\n\n" for k, v in content_results.items()])
        final_report = f"""# 마케팅 분석 최종 리포트

## 원본 요청
{user_request}

## Planner 분석
{planner_result}

## Data Team 분석 결과
{combined_data}

## Content Team 결과물
{content_section}

## Reviewer 검토 결과
{reviewer_result}
"""
        logger.save_output("final", final_report, "final_report.md")
        logger.log("system", LogLevel.INFO, "✅ 워크플로우 완료!")
        
        return final_report


def run_in_background(team: MarketingAgentTeam, request: str):
    """백그라운드에서 워크플로우 실행"""
    thread = threading.Thread(target=team.run_workflow, args=(request,))
    thread.daemon = True
    thread.start()
    return thread


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Marketing Agent Team")
    parser.add_argument("--test", action="store_true", help="테스트 모드 실행")
    parser.add_argument("--query", type=str, default="에어팟 맥스 마케팅 분석", help="분석 요청")
    args = parser.parse_args()
    
    team = MarketingAgentTeam()
    
    if args.test:
        print("\n🧪 테스트 모드: 에이전트 로딩 확인")
        for team_name, agents in team.agents.items():
            print(f"\n[{team_name}]")
            for agent in agents:
                print(f"  ✓ {agent.name}")
    else:
        team.run_workflow(args.query)
