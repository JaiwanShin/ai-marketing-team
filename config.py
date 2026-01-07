"""
config.py - Agent Configuration Loader

Markdown 파일에서 에이전트 프롬프트를 로드하고
LLM에 전달할 수 있는 형식으로 변환합니다.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """에이전트 설정"""
    name: str
    role: str
    goal: str
    backstory: str
    instructions: str
    output_format: str
    raw_content: str


def load_agent_config(filepath: str) -> AgentConfig:
    """
    Markdown 파일에서 에이전트 설정을 로드합니다.
    
    Args:
        filepath: 에이전트 정의 MD 파일 경로
    
    Returns:
        AgentConfig 객체
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 섹션 파싱
    sections = {}
    current_section = None
    current_content = []
    
    for line in content.split("\n"):
        if line.startswith("## "):
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = line[3:].strip().lower()
            current_content = []
        elif line.startswith("# "):
            sections["title"] = line[2:].strip()
        else:
            current_content.append(line)
    
    if current_section:
        sections[current_section] = "\n".join(current_content).strip()
    
    # 파일명에서 에이전트 이름 추출
    name = Path(filepath).stem.replace("-", "_")
    
    return AgentConfig(
        name=name,
        role=sections.get("role", ""),
        goal=sections.get("goal", ""),
        backstory=sections.get("backstory", ""),
        instructions=sections.get("instructions", ""),
        output_format=sections.get("output format", ""),
        raw_content=content
    )


def load_all_agents(base_dir: str = "agents") -> dict[str, list[AgentConfig]]:
    """
    모든 에이전트 설정을 팀별로 로드합니다.
    
    Args:
        base_dir: agents 디렉토리 경로
    
    Returns:
        팀별 에이전트 목록 딕셔너리
    """
    agents = {}
    base_path = Path(base_dir)
    
    for team_dir in base_path.iterdir():
        if team_dir.is_dir():
            team_name = team_dir.name
            agents[team_name] = []
            
            for agent_file in team_dir.glob("*.md"):
                config = load_agent_config(str(agent_file))
                agents[team_name].append(config)
    
    return agents


def load_skill(filepath: str) -> str:
    """
    스킬 Markdown 파일을 로드합니다.
    
    Args:
        filepath: 스킬 MD 파일 경로
    
    Returns:
        스킬 내용 (문자열)
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def build_system_prompt(agent: AgentConfig, skills: list[str] = None) -> str:
    """
    에이전트 설정을 시스템 프롬프트로 변환합니다.
    
    Args:
        agent: 에이전트 설정
        skills: 추가할 스킬 내용 목록
    
    Returns:
        시스템 프롬프트 문자열
    """
    prompt_parts = [
        f"# {agent.name}",
        "",
        f"## Role\n{agent.role}",
        "",
        f"## Goal\n{agent.goal}",
        "",
        f"## Backstory\n{agent.backstory}",
        "",
        f"## Instructions\n{agent.instructions}",
        "",
        f"## Output Format\n{agent.output_format}",
    ]
    
    if skills:
        prompt_parts.append("")
        prompt_parts.append("## Available Skills/Tools")
        for skill in skills:
            prompt_parts.append(skill)
    
    return "\n".join(prompt_parts)


if __name__ == "__main__":
    # 테스트
    agents = load_all_agents()
    for team, agent_list in agents.items():
        print(f"\n=== {team} ===")
        for agent in agent_list:
            print(f"  - {agent.name}: {agent.role[:50]}...")
