"""
dashboard.py - Live Monitoring Dashboard

에이전트 팀의 실행 상태를 실시간으로 모니터링합니다.
새로고침 없이 자동으로 갱신됩니다.

실행: streamlit run dashboard.py
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from pathlib import Path
from datetime import datetime
import json

from logger import AgentLogger
from main import MarketingAgentTeam, run_in_background


# ============================================
# 페이지 설정
# ============================================
st.set_page_config(
    page_title="🎯 Data Marketing Agent Team",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# 자동 갱신 (1초마다)
# ============================================
count = st_autorefresh(interval=1000, limit=None, key="live_refresh")

# ============================================
# CSS 스타일링
# ============================================
st.markdown("""
<style>
    .status-box {
        padding: 1rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-bottom: 1rem;
    }
    .status-idle {
        background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
    }
    .status-running {
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
    }
    .log-container {
        background: #1e1e1e;
        color: #00ff00;
        font-family: 'Consolas', 'Monaco', monospace;
        padding: 1rem;
        border-radius: 5px;
        height: 300px;
        overflow-y: auto;
        font-size: 0.85rem;
    }
    .agent-card {
        padding: 0.5rem 1rem;
        border-radius: 8px;
        margin: 0.25rem 0;
        background: #f8f9fa;
        border-left: 4px solid #667eea;
    }
    .agent-active {
        border-left-color: #00ff00;
        background: #e8f5e9;
    }
    .agent-done {
        border-left-color: #28a745;
        background: #d4edda;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# 세션 상태 초기화
# ============================================
if "team" not in st.session_state:
    st.session_state.team = None
if "running" not in st.session_state:
    st.session_state.running = False
if "thread" not in st.session_state:
    st.session_state.thread = None

# ============================================
# 사이드바 - 입력 및 제어
# ============================================
with st.sidebar:
    st.title("🎯 Agent Team Control")
    st.divider()
    
    # 분석 요청 입력
    query = st.text_area(
        "📝 분석 요청",
        placeholder="예: 에어팟 맥스 마케팅 분석",
        height=100
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        run_button = st.button("▶️ 실행", type="primary", use_container_width=True)
    
    with col2:
        clear_button = st.button("🗑️ 초기화", use_container_width=True)
    
    if run_button and query and not st.session_state.running:
        # 팀 초기화
        if st.session_state.team is None:
            st.session_state.team = MarketingAgentTeam()
        
        # 백그라운드 실행
        st.session_state.running = True
        st.session_state.thread = run_in_background(st.session_state.team, query)
        st.toast("🚀 워크플로우 시작!", icon="🚀")
    
    if clear_button:
        logger = AgentLogger()
        logger.clear_logs()
        
        # outputs 폴더 정리
        outputs_dir = Path("outputs")
        for f in outputs_dir.glob("*.md"):
            f.unlink()
        for f in outputs_dir.glob("*.jsonl"):
            f.unlink()
        
        st.session_state.running = False
        st.toast("🗑️ 초기화 완료!", icon="✅")
    
    st.divider()
    
    # 팀 구성 표시
    st.subheader("👥 Team Structure")
    
    team_structure = {
        "🎯 Orchestrator": ["planner", "reviewer"],
        "📊 Data Team": ["trend_analyst", "keyword_researcher", "price_monitor", "review_analyst"],
        "✍️ Content Team": ["product_copywriter", "report_generator"]
    }
    
    logger = AgentLogger()
    status = logger.get_status()
    current_agent = status.get("current_agent")
    
    for team_name, agents in team_structure.items():
        st.caption(team_name)
        for agent in agents:
            if agent == current_agent:
                st.markdown(f"<div class='agent-card agent-active'>🔄 {agent}</div>", unsafe_allow_html=True)
            else:
                # 완료된 에이전트 확인
                output_file = Path("outputs") / f"{agent}_output.md"
                if output_file.exists():
                    st.markdown(f"<div class='agent-card agent-done'>✅ {agent}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='agent-card'>⏳ {agent}</div>", unsafe_allow_html=True)

# ============================================
# 메인 영역
# ============================================
st.title("🎯 Data Marketing Agent Team Dashboard")

# 상태 표시
logger = AgentLogger()
status = logger.get_status()

col1, col2, col3 = st.columns(3)

with col1:
    current = status.get("current_agent") or "대기 중"
    st.metric("🤖 현재 에이전트", current)

with col2:
    st.metric("📊 상태", status.get("current_status", "대기 중"))

with col3:
    if status.get("started_at"):
        started = datetime.fromisoformat(status["started_at"])
        elapsed = (datetime.now() - started).seconds
        st.metric("⏱️ 경과 시간", f"{elapsed}초")
    else:
        st.metric("⏱️ 경과 시간", "-")

st.divider()

# ============================================
# 결과물 탭
# ============================================
st.subheader("📁 에이전트 결과물")

outputs_dir = Path("outputs")
output_files = list(outputs_dir.glob("*_output.md"))

if output_files:
    # 탭 이름 정리
    tab_names = [f.stem.replace("_output", "") for f in output_files]
    tabs = st.tabs(tab_names)
    
    for tab, file in zip(tabs, output_files):
        with tab:
            try:
                content = file.read_text(encoding="utf-8")
                st.markdown(content)
            except Exception as e:
                st.error(f"파일 읽기 오류: {e}")
else:
    st.info("아직 생성된 결과물이 없습니다. 분석을 실행해주세요.")

st.divider()

# ============================================
# 실시간 로그
# ============================================
st.subheader("📜 실시간 로그")

logs = logger.get_logs(limit=100)

if logs:
    # 로그를 역순으로 표시 (최신이 위로)
    log_lines = []
    for log in reversed(logs[-30:]):  # 최근 30개만
        timestamp = log.get("timestamp", "")[-8:]  # HH:MM:SS
        agent = log.get("agent_name", "system")
        level = log.get("level", "INFO")
        message = log.get("message", "")
        
        # 레벨별 색상
        color = {
            "INFO": "#00ff00",
            "THINKING": "#ffff00",
            "ACTION": "#00ffff",
            "OUTPUT": "#ff00ff",
            "ERROR": "#ff0000"
        }.get(level, "#ffffff")
        
        log_lines.append(f'<span style="color:{color}">[{timestamp}] [{agent}] {message}</span>')
    
    log_html = "<br>".join(log_lines)
    st.markdown(f"<div class='log-container'>{log_html}</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='log-container'>로그를 기다리는 중...</div>", unsafe_allow_html=True)

# ============================================
# 실행 완료 감지
# ============================================
if st.session_state.running:
    # 스레드가 완료되었는지 확인
    if st.session_state.thread and not st.session_state.thread.is_alive():
        st.session_state.running = False
        st.balloons()
        st.success("🎉 워크플로우가 완료되었습니다!")

# ============================================
# 푸터
# ============================================
st.divider()
st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 자동 갱신 #{count}")
