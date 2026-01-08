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


class MarketingAgentTeam:
    """데이터 마케팅 에이전트 팀"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: OpenAI API 키 (환경변수 OPENAI_API_KEY 사용 가능)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.agents = load_all_agents()
        self.skills = self._load_skills()
        
        # LLM 클라이언트 초기화
        # self.client = OpenAI(api_key=self.api_key)
        
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
    
    def _call_llm(self, agent: AgentConfig, user_message: str, skills: list[str] = None) -> str:
        """
        LLM 호출 (실제 구현 시 주석 해제)
        
        지금은 시뮬레이션 모드로 동작합니다.
        """
        system_prompt = build_system_prompt(agent, skills)
        
        # 실제 LLM 호출
        # response = self.client.chat.completions.create(
        #     model="gpt-4o",
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_message}
        #     ],
        #     temperature=0.7
        # )
        # return response.choices[0].message.content
        
        # 시뮬레이션 모드
        time.sleep(2)  # LLM 호출 시뮬레이션
        return f"# {agent.name} 분석 결과\n\n[시뮬레이션 모드] {agent.role[:100]}...\n\n이 부분은 실제 LLM 응답으로 대체됩니다."
    
    def run_agent(self, team: str, agent_name: str, task: str) -> str:
        """단일 에이전트 실행"""
        agent = self._get_agent(team, agent_name)
        if not agent:
            raise ValueError(f"Agent not found: {team}/{agent_name}")
        
        logger.set_current_agent(agent_name, f"{agent_name} 작업 중...")
        logger.log(agent_name, LogLevel.THINKING, f"📋 작업 수신: {task[:50]}...")
        
        # 관련 스킬 결정
        skills_to_use = []
        if agent_name in ["keyword_researcher"]:
            skills_to_use.append(self.skills.get("search_ad", ""))
        elif agent_name in ["price_monitor", "review_analyst"]:
            skills_to_use.append(self.skills.get("shopping", ""))
        elif agent_name in ["trend_analyst"]:
            skills_to_use.append(self.skills.get("datalab", ""))
        
        logger.log(agent_name, LogLevel.ACTION, "🤖 LLM 호출 중...")
        result = self._call_llm(agent, task, skills_to_use)
        
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
