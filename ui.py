import streamlit as st
import requests
import time
from datetime import datetime as dt
import textwrap

# --- GLOBAL LAYOUT CONFIGURATION ---
st.set_page_config(
    layout="wide", 
    initial_sidebar_state="collapsed", 
    page_title="Physics Tutor"
)

# SINGLE-CONTAINER ROUTING:
# Streamlit connects directly to FastAPI internally on Port 8000.
BACKEND_URL = "http://127.0.0.1:8000"

# --- STATE MANAGEMENT & RECOVERY ---
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "current_question_id" not in st.session_state:
    st.session_state.current_question_id = "00899"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Welcome. I'm ready to help you work through this physics problem. Where would you like to start?"}
    ]
if "insights" not in st.session_state:
    st.session_state.insights = []
if "question_context" not in st.session_state:
    st.session_state.question_context = ""
if "tutoring_mode" not in st.session_state:
    st.session_state.tutoring_mode = "Active — Socratic Mode"


def sync_session_snapshot(session_id: str):
    """Syncs session state dynamically from backend."""
    try:
        base_url = BACKEND_URL.rstrip("/")
        res = requests.get(f"{base_url}/session/{session_id}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.session_state.chat_history = data.get("chat_history") or []
            st.session_state.insights = data.get("notebook_history") or []
            mode = data.get("tutoring_mode", "socratic")
            st.session_state.tutoring_mode = "Active — Socratic Mode" if mode == "socratic" else "Active — Direct Mode"
        else:
            st.error(f"Failed to synchronize workspace state. Server returned code {res.status_code}.")
            st.stop()
    except Exception as e:
        st.error(f"Internal container sync failed: {e}")
        st.stop()


def init_session(q_id: str):
    """
    Initializes session on Port 8000.
    10-retry warmup buffer handles FastAPI startup caching delays silently.
    """
    base_url = BACKEND_URL.rstrip("/")
    url = f"{base_url}/session/start/{q_id.strip()}"
    
    max_retries = 10
    for attempt in range(max_retries):
        try:
            res = requests.post(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                st.session_state.session_id = data.get("session_id")
                st.session_state.current_question_id = data.get("question_id")
                st.session_state.question_context = data.get("context")
                st.session_state.chat_history = [
                    {"role": "assistant", "content": "Welcome to the workspace. Let's step through this physics problem together. How can I help you resolve the active step?"}
                ]
                st.session_state.insights = []
                st.session_state.tutoring_mode = "Active — Socratic Mode"
                return  # Connection successful, exit function
            else:
                st.error(f"Internal initialization failed (Status {res.status_code}).")
                st.stop()
        except requests.exceptions.ConnectionError:
            # Silence warmup warnings during the first 3 container boot attempts
            if attempt < max_retries - 1:
                if attempt >= 3:
                    st.warning(f"Connecting to physics tutor engine... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(3)
            else:
                st.error("Error: Could not spin up the physics tutor state engine on GCP.")
                st.stop()
        except Exception as e:
            st.error(f"Internal API handshake failed: {e}")
            st.stop()


# --- DYNAMIC BACKEND NAVIGATION ---
def navigate(direction: str):
    try:
        base_url = BACKEND_URL.rstrip("/")
        res = requests.get(f"{base_url}/questions/navigate/{st.session_state.current_question_id}/{direction}", timeout=5)
        if res.status_code == 200:
            next_q_id = res.json().get("question_id")
            if next_q_id:
                init_session(next_q_id)
                st.rerun()
        else:
            st.error("Navigation failed: Unable to fetch next problem state from GCP API.")
    except Exception as e:
        st.error(f"Internal navigation failed: {e}")


# --- INITIALIZATION RUNNER ---
if st.session_state.session_id is None:
    init_session(st.session_state.current_question_id)
else:
    sync_session_snapshot(st.session_state.session_id)


# --- PREMIUM SYSTEM STYLING (YOUR CUSTOM SPECIFICATIONS) ---
st.markdown(textwrap.dedent("""
<style>
  /* Import Google Fonts directly */
  @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');

  /* Base editorial setup */
  html, body, [data-testid="stAppViewContainer"] {
    background-color: #FAFAF9 !important;
    color: #121212 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    -webkit-font-smoothing: antialiased;
  }
  
  /* Strip Streamlit system garbage */
  header, footer, #MainMenu { display: none !important; }
  .block-container { padding: 1.5rem 0rem !important; max-width: 100% !important; }

  /* Premium Top Navigation Bar Container */
  .top-bar-container {
    background-color: #FFFFFF;
    border-bottom: 1px solid #EAE8E3;
    padding-bottom: 1rem;
    margin-bottom: 2rem;
    padding-left: 4%;
    padding-right: 4%;
  }

  .top-bar-title {
    font-size: 0.8rem;
    font-weight: 500;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #121212;
    margin-top: 10px;
  }

  /* Flex center top navigation alignment */
  .top-bar-center {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1.5rem;
    margin-top: 8px;
  }

  .problem-indicator {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.8rem;
    font-weight: 600;
    border-bottom: 1.5px solid #121212;
    color: #121212;
    padding-bottom: 4px;
    letter-spacing: 0.05em;
  }

  .top-bar-right-links {
    font-size: 0.75rem;
    font-weight: 600;
    color: #121212;
    letter-spacing: 0.08em;
    text-align: right;
    margin-top: 10px;
    display: flex;
    justify-content: flex-end;
    gap: 1.5rem;
  }

  /* Left Panel Workspace Typography and Tags */
  .tag { 
    font-size: 0.7rem; 
    font-weight: 600; 
    color: #90908C; 
    letter-spacing: 0.12em; 
    text-transform: uppercase; 
    margin-bottom: 1.25rem; 
  }
  .title { 
    font-family: 'EB Garamond', serif;
    font-size: 1.8rem; 
    font-weight: 400; 
    letter-spacing: -0.01em; 
    color: #121212; 
    margin-bottom: 1.5rem; 
  }
  
  /* Forces markdown text to style as EB Garamond serif, preserving LaTeX math parsing */
  .workspace-sheet .stMarkdown p {
    font-family: 'EB Garamond', serif !important;
    font-size: 17px !important;
    line-height: 1.8 !important;
    color: #121212 !important;
  }

  /* Study Notebook Elements - Active Crisp B&W Slate */
  .notebook-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    margin-top: 3rem;
    border-top: 1px solid #EAE8E3;
    padding-top: 2rem;
  }
  .notebook-title {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #5A5A57;
  }
  .notebook-container {
    border: 1.5px solid #121212;
    border-radius: 6px;
    padding: 2.5rem 2rem;
    background-color: #FFFFFF;
    text-align: left;
    min-height: 120px;
    display: flex;
    align-items: center;
    justify-content: flex-start;
  }
  .notebook-placeholder {
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #5A5A57;
    font-size: 0.85rem;
    line-height: 1.5;
  }
  .notebook-card {
    border: 1.5px solid #121212;
    border-radius: 6px;
    padding: 1.5rem 2rem;
    margin-bottom: 1rem;
    text-align: left;
    background-color: #FFFFFF;
  }
  .card-label {
    font-size: 0.65rem; 
    font-weight: 700; 
    color: #90908C; 
    text-transform: uppercase; 
    letter-spacing: 0.04em;
  }
  .card-value {
    font-family: 'EB Garamond', serif; 
    font-size: 1.2rem; 
    font-weight: 500;
    margin-top: 5px; 
    color: #121212;
  }
  .card-meta {
    font-size: 0.78rem; 
    color: #5A5A57; 
    margin-top: 6px;
  }

  /* Minimalist Chat panel divider logic on the right-hand column */
  .right-chat-panel {
    border-left: 1px solid #EAE8E3;
    padding-left: 1.75rem;
    min-height: 75vh;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
  }
  
  .chat-mode-header {
    text-align: left;
    font-size: 0.75rem;
    font-weight: 700;
    color: #90908C;
    margin-bottom: 0.2rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }
  
  .chat-mode-subheader {
    text-align: left;
    font-size: 0.72rem;
    font-weight: 500;
    color: #90908C;
    margin-bottom: 0.5rem;
  }

  /* Dialogue formatting matching your exact specification */
  .msg-wrapper {
    margin-bottom: 2rem;
    text-align: left;
  }
  .msg-sender-label {
    font-size: 0.72rem;
    font-weight: 700;
    color: #90908C;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .msg-content-text {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 13px;
    line-height: 1.6;
    color: #121212;
  }
  
  /* Socrates left-border accent override */
  .msg-wrapper.system .msg-content-text {
    font-family: 'EB Garamond', serif !important;
    font-size: 14px;
    border-left: 1.5px solid #121212;
    padding-left: 0.75rem;
    line-height: 1.6;
  }
  
  .status-indicator {
    font-family: 'EB Garamond', serif;
    font-style: italic;
    color: #90908C;
    font-size: 13px;
    margin-top: 1.5rem;
  }

  /* Completely strip Streamlit's default bubble and container designs */
  div[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin-bottom: 1.5rem !important;
  }

  /* Clean up Streamlit native buttons to act as flat text links */
  div.stButton > button {
    border: none !important;
    background-color: transparent !important;
    color: #90908C !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    padding: 0px !important;
    transition: opacity 0.15s ease;
    line-height: 1 !important;
    height: auto !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  div.stButton > button:hover {
    opacity: 0.7;
    color: #121212 !important;
    background-color: transparent !important;
  }
  
  /* Horizontal line divider on the right column */
  .chat-header-divider {
    border-bottom: 1px solid #EAE8E3;
    margin-bottom: 2rem;
    margin-top: 0.8rem;
  }

  /* Premium borderless input matching Image 2 */
  [data-testid="stChatInput"] {
    border: none !important;
    border-bottom: 1.5px solid #121212 !important;
    border-radius: 0px !important;
    background: #FFFFFF !important;
    padding: 0.2rem 0rem !important;
  }
</style>
"""), unsafe_allow_html=True)


# --- X. PIXEL-PERFECT NATIVE HEADER ---
st.markdown('<div class="top-bar-container">', unsafe_allow_html=True)
h_col_left, h_col_center, h_col_right = st.columns([2, 5, 2])

with h_col_left:
    st.markdown('<div class="top-bar-title">PHYSICS TUTOR</div>', unsafe_allow_html=True)

with h_col_center:
    st.markdown('<div class="top-bar-center">', unsafe_allow_html=True)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    with nav_col1:
        st.button("Prev", on_click=lambda: navigate("prev"))
    with nav_col2:
        st.markdown(f'<div style="text-align: center;"><span class="problem-indicator">cal_problem_{st.session_state.current_question_id}</span></div>', unsafe_allow_html=True)
    with nav_col3:
        st.button("Next", on_click=lambda: navigate("next"))
    st.markdown('</div>', unsafe_allow_html=True)

with h_col_right:
    st.markdown('<div class="top-bar-right-links"><span>UPLOAD</span><span>EXIT</span></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# --- XI. THE NEW 7% / 60% / 8% / 25% GRID SPLIT ---
col_space1, col_workspace, col_space2, col_chat = st.columns([0.07, 0.60, 0.08, 0.25])


# ==========================================
# COLUMN 1: LEFT BREATHING MARGIN (7%)
# ==========================================
with col_space1:
    st.empty()


# ==========================================
# COLUMN 2: WORKSPACE CONTAINER (60%)
# ==========================================
with col_workspace:
    st.markdown('<div class="workspace-sheet">', unsafe_allow_html=True)
    
    st.markdown('<div class="tag">Physics / Class 12 / Electromagnetic Induction</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="title">Problem {st.session_state.current_question_id}</div>', unsafe_allow_html=True)
    
    # PROBLEM SHEET: Native Markdown forces perfect mathematical equation parsing
    st.markdown(st.session_state.question_context)
    
    # Study Notebook Section (Pushed Directly Under Problem Description)
    insight_count = len(st.session_state.insights)
    st.markdown(f"""
    <div class="notebook-header-row">
        <div class="notebook-title">Active Study Notebook</div>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.insights:
        st.markdown("""
        <div class="notebook-container">
            <div class="notebook-placeholder">No insights recorded yet. Solve steps in the chat to populate this area.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        rendered_steps = set()
        for insight in st.session_state.insights:
            step_key = insight.get("step_key", "")
            if step_key in rendered_steps:
                continue
            rendered_steps.add(step_key)
            st.markdown(f"""
            <div class="notebook-card">
                <div class="card-label">{insight.get('theorem', 'Unlocked Step')}</div>
                <div class="card-value">{insight.get('formula', '')}</div>
                <div class="card-meta">Target value verified: {insight.get('result', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# COLUMN 3: MIDDLE GAP SPACE (8% - seamlessly aligned with workspace)
# ==========================================
with col_space2:
    st.empty()


# ==========================================
# COLUMN 4: MINIMALIST PIXEL-PERFECT CHAT (25%)
# ==========================================
with col_chat:
    st.markdown('<div class="right-chat-panel">', unsafe_allow_html=True)
    
    # Header Info Block
    st.markdown('<div class="chat-mode-header">Dialogue Assistant</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chat-mode-subheader">Active — {st.session_state.tutoring_mode}</div>', unsafe_allow_html=True)
    st.markdown('<div class="chat-header-divider"></div>', unsafe_allow_html=True)
    
    # Clean Dialogue Stream
    chat_container = st.container(height=450, border=False)
    
    with chat_container:
        for msg in st.session_state.chat_history:
            sender = "Socrates" if msg["role"] == "assistant" or msg["role"] == "tutor" else "You"
            wrapper_class = "msg-wrapper system" if sender == "Socrates" else "msg-wrapper"
            st.markdown(f"""
            <div class="{wrapper_class}">
                <div class="msg-sender-label">{sender}</div>
                <div class="msg-content-text">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
            
    # Minimal Chat Input pinned at the base with target bottom-border overrides
    user_input = st.chat_input("Ask a question...")
    
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with chat_container:
            st.markdown(f"""
            <div class="msg-wrapper">
                <div class="msg-sender-label">You</div>
                <div class="msg-content-text">{user_input}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Subtle loading text during API request lifecycle
            status_placeholder = st.markdown('<div class="status-indicator">Socrates is processing...</div>', unsafe_allow_html=True)
            
            try:
                base_url = BACKEND_URL.rstrip("/")
                response = requests.post(
                    f"{base_url}/chat/{st.session_state.session_id}",
                    json={"user_text": user_input},
                    timeout=15
                )
                status_placeholder.empty() # Remove loader smoothly
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("ai_response", "I'm having trouble analyzing this step.")
                    
                    backend_mode = data.get("phase", "SOCRATIC")
                    st.session_state.tutoring_mode = "Socratic Mode" if backend_mode == "SOCRATIC" else "Direct Mode"
                    
                    nb_updates = data.get("notebook_updates", {})
                    if nb_updates and nb_updates.get("official_solution"):
                        st.session_state.insights.append(nb_updates["official_solution"])
                else:
                    ai_response = f"GCP Engine Error: code {response.status_code}."
            except Exception as e:
                status_placeholder.empty()
                ai_response = f"GCP Synchronizer Error: unable to connect to API gateway."
            
            st.markdown(f"""
            <div class="msg-wrapper system">
                <div class="msg-sender-label">Socrates</div>
                <div class="msg-content-text">{ai_response}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)
