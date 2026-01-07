"""
logger.py - Real-time Agent Logger

각 에이전트의 실행 로그를 실시간으로 파일에 저장합니다.
대시보드에서 이 파일을 읽어 라이브 모니터링합니다.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(str, Enum):
    INFO = "INFO"
    THINKING = "THINKING"
    ACTION = "ACTION"
    OUTPUT = "OUTPUT"
    ERROR = "ERROR"


@dataclass
class LogEntry:
    """로그 엔트리"""
    timestamp: str
    agent_name: str
    level: LogLevel
    message: str
    data: Optional[dict] = None


class AgentLogger:
    """에이전트 실시간 로거"""
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 로그 파일 경로
        self.log_file = self.output_dir / "agent_logs.jsonl"
        self.status_file = self.output_dir / "status.json"
        
        # 초기화
        self._init_status()
    
    def _init_status(self):
        """상태 파일 초기화"""
        status = {
            "current_agent": None,
            "current_status": "대기 중",
            "started_at": None,
            "last_update": datetime.now().isoformat()
        }
        self._write_status(status)
    
    def _write_status(self, status: dict):
        """상태 파일 저장"""
        with open(self.status_file, "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
    
    def _append_log(self, entry: LogEntry):
        """로그 추가"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
    
    def set_current_agent(self, agent_name: str, status: str = "작업 중"):
        """현재 작업 중인 에이전트 설정"""
        status_data = {
            "current_agent": agent_name,
            "current_status": status,
            "started_at": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat()
        }
        self._write_status(status_data)
        
        self.log(agent_name, LogLevel.INFO, f"🚀 {agent_name} 시작")
    
    def log(
        self,
        agent_name: str,
        level: LogLevel,
        message: str,
        data: Optional[dict] = None
    ):
        """로그 기록"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            agent_name=agent_name,
            level=level,
            message=message,
            data=data
        )
        self._append_log(entry)
        
        # 상태 업데이트
        self._update_last_activity()
    
    def _update_last_activity(self):
        """마지막 활동 시간 업데이트"""
        try:
            with open(self.status_file, "r", encoding="utf-8") as f:
                status = json.load(f)
            status["last_update"] = datetime.now().isoformat()
            self._write_status(status)
        except:
            pass
    
    def save_output(self, agent_name: str, content: str, filename: str = None):
        """에이전트 결과물 저장"""
        if filename is None:
            filename = f"{agent_name}_output.md"
        
        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.log(agent_name, LogLevel.OUTPUT, f"📄 결과물 저장: {filename}")
        return str(output_path)
    
    def complete_agent(self, agent_name: str):
        """에이전트 작업 완료"""
        self.log(agent_name, LogLevel.INFO, f"✅ {agent_name} 완료")
        
        status = {
            "current_agent": None,
            "current_status": "대기 중",
            "started_at": None,
            "last_update": datetime.now().isoformat()
        }
        self._write_status(status)
    
    def get_logs(self, limit: int = 100) -> list[dict]:
        """최근 로그 조회"""
        if not self.log_file.exists():
            return []
        
        logs = []
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        
        return logs[-limit:]
    
    def get_status(self) -> dict:
        """현재 상태 조회"""
        if not self.status_file.exists():
            return {"current_agent": None, "current_status": "초기화 필요"}
        
        try:
            with open(self.status_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {"current_agent": None, "current_status": "대기 중"}
                return json.loads(content)
        except (json.JSONDecodeError, Exception):
            return {"current_agent": None, "current_status": "대기 중"}
    
    def clear_logs(self):
        """로그 초기화"""
        if self.log_file.exists():
            self.log_file.unlink()
        self._init_status()


# 전역 로거 인스턴스
logger = AgentLogger()


if __name__ == "__main__":
    # 테스트
    logger.set_current_agent("planner", "분석 계획 수립 중")
    logger.log("planner", LogLevel.THINKING, "사용자 요청을 분석 중...")
    logger.log("planner", LogLevel.ACTION, "Data Team에 지시사항 전달")
    logger.save_output("planner", "# 분석 계획\n\n테스트 내용")
    logger.complete_agent("planner")
    
    print("Logs:", logger.get_logs())
    print("Status:", logger.get_status())
