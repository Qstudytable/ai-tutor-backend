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
        {"role": "assistant", "content": "Welcome to the workspace. Let's step through this physics problem together. How can I help you resolve the active step?"}
    ]
if "insights" not in st.session_state:
    st.session_state.insights = []
if "question_context" not in st.session_state:
    st.session_state.question_context = ""
if "tutoring_mode" not in st.session_state:
    st.session_state.tutoring_mode = "Socratic Mode"


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
            st.session_state.tutoring_mode = "Socratic Mode" if mode == "socratic" else "Direct Mode"
        else:
            st.error(f"Failed to synchronize workspace state. Server returned code {res.status_code}.")
            st.stop()
    except Exception as e:
        st.error(f"Internal container sync failed: {e}")
        st.stop()


def init_session(q_id: str):
    """Initializes session on Port 8000. Automatically handles backend warmups."""
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
                st.session_state.tutoring_mode = "Socratic Mode"
                return  # Connection successful, exit function
            else:
                st.error(f"Internal initialization failed (Status {res.status_code}).")
                st.stop()
        except requests.exceptions.ConnectionError:
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


# --- EDITORIAL SYSTEM STYLING ---
st.markdown(textwrap.dedent("""
<style>
  /* Base editorial setup */
  html, body, [data-testid="stAppViewContainer"] {
    background-color: #FFFFFF !important;
    color: #1D1D1F !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }
  
  /* Strip out standard dashboard margins and headers */
  header, footer, #MainMenu { display: none !important; }
  .block-container { padding: 1.5rem 0rem !important; max-width: 100% !important; }

  /* Premium Top Navigation Bar Container */
  .top-bar-container {
    border-bottom: 1px solid #1D1D1F;
    padding-bottom: 1rem;
    margin-bottom: 2rem;
    padding-left: 7%;
    padding-right: 7%;
  }

  .top-bar-title {
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #1D1D1F;
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
    font-family: -apple-system, sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    border-bottom: 2px solid #1D1D1F;
    color: #1D1D1F;
    padding-bottom: 4px;
    letter-spacing: 0.02em;
  }

  .top-bar-right-links {
    font-size: 0.78rem;
    font-weight: 600;
    color: #1D1D1F;
    letter-spacing: 0.08em;
    text-align: right;
    margin-top: 10px;
    display: flex;
    justify-content: flex-end;
    gap: 1.5rem;
  }

  /* Left Panel Workspace Typography and Tags */
  .tag { 
    font-size: 0.68rem; 
    font-weight: 600; 
    color: #86868B; 
    letter-spacing: 0.08em; 
    text-transform: uppercase; 
    margin-bottom: 0.8rem; 
  }
  .title { 
    font-size: 1.8rem; 
    font-weight: 600; 
    letter-spacing: -0.01em; 
    color: #1D1D1F; 
    margin-bottom: 1.5rem; 
  }
  
  /* Forces markdown text to style as Georgia serif, preserving LaTeX math parsing */
  .stMarkdown p {
    font-family: Georgia, "Times New Roman", Times, serif !important;
    font-size: 1.15rem !important;
    line-height: 1.8 !important;
    color: #1D1D1F !important;
  }
  
  /* Active Concept metadata box with a left vertical border line */
  .active-concept-section {
    border-left: 2px solid #1D1D1F;
    padding-left: 1.2rem;
    margin: 2rem 0;
  }
  .active-concept-label {
    font-size: 0.62rem;
    font-weight: 700;
    color: #86868B;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
  }
  .active-concept-desc {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 1rem;
    line-height: 1.6;
    color: #1D1D1F;
  }

  /* Study Notebook Elements */
  .notebook-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    margin-top: 2rem;
    border-top: 1px solid #F0F0F2;
    padding-top: 1.5rem;
  }
  .notebook-title {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #1D1D1F;
  }
  .notebook-container {
    border: 1px solid #E5E5EA;
    border-radius: 4px;
    padding: 3rem 1.5rem;
    background-color: #F9F9FB;
    text-align: center;
    min-height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .notebook-placeholder {
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    color: #86868B;
    font-size: 0.85rem;
  }
  .notebook-card {
    border: 1px solid #E5E5EA;
    border-radius: 4px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    text-align: left;
    background-color: #FFFFFF;
  }

  /* Minimalist Chat panel divider logic on the right-hand column */
  .right-chat-panel {
    border-left: 1px solid #E5E5EA;
    padding-left: 2rem;
    min-height: 75vh;
  }
  
  .chat-mode-header {
    text-align: left;
    font-size: 0.82rem;
    font-weight: 700;
    color: #1D1D1F;
    margin-bottom: 0.2rem;
    letter-spacing: 0.04em;
  }
  
  .chat-mode-subheader {
    text-align: left;
    font-size: 0.72rem;
    font-weight: 500;
    color: #86868B;
    margin-bottom: 2rem;
  }

  /* Socrates Light Gray Message Bubble (Image 2 style) */
  .msg-socrates-card {
    background-color: #F5F5F7;
    border-radius: 8px;
    padding: 15px 20px;
    margin-bottom: 1.5rem;
    font-size: 0.95rem;
    line-height: 1.6;
    color: #1D1D1F;
    max-width: 90%;
  }

  /* You Solid Black Message Bubble (Image 2 style) */
  .msg-you-card {
    background-color: #000000;
    color: #FFFFFF !important;
    border-radius: 8px;
    padding: 15px 20px;
    margin-bottom: 1.5rem;
    font-size: 0.95rem;
    line-height: 1.6;
    max-width: 90%;
    margin-left: auto; /* Right-aligns the block perfectly */
    text-align: left;
  }

  .msg-sender-label-socrates {
    font-size: 0.68rem;
    font-weight: 700;
    color: #86868B;
    margin-bottom: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .msg-sender-label-you {
    font-size: 0.68rem;
    font-weight: 700;
    color: #86868B;
    margin-bottom: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    text-align: right;
  }

  .status-indicator {
    font-family: -apple-system, sans-serif;
    font-style: italic;
    color: #86868B;
    font-size: 0.85rem;
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
    color: #86868B !important;
    font-family: -apple-system, sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 0px !important;
    transition: color 0.2s ease;
    line-height: 1 !important;
    height: auto !important;
  }
  div.stButton > button:hover {
    color: #1D1D1F !important;
    background-color: transparent !important;
  }
  
  /* Horizontal line divider on the right column */
  .chat-header-divider {
    border-bottom: 1px solid #E5E5EA;
    margin-bottom: 2rem;
    margin-top: 0.5rem;
  }

  /* Premium borderless input matching Image 2 */
  [data-testid="stChatInput"] {
    border: none !important;
    border-bottom: 1px solid #1D1D1F !important;
    border-radius: 0px !important;
    background: #FFFFFF !important;
    padding: 0.2rem 0rem !important;
  }
</style>
"""), unsafe_allow_html=True)


# --- VI. PIXEL-PERFECT NATIVE HEADER ---
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


# --- VII. THE 10% / 60% / 10% / 20% GRID ---
col_space1, col_workspace, col_space2, col_chat = st.columns([0.10, 0.60, 0.10, 0.20])


# ==========================================
# COLUMN 1: LEFT BREATHING MARGIN (10%)
# ==========================================
with col_space1:
    st.empty()


# ==========================================
# COLUMN 2: WORKSPACE SHEET (60%)
# ==========================================
with col_workspace:
    st.markdown('<div class="tag">Physics / Class 12 / Electromagnetic Induction</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="title">Problem {st.session_state.current_question_id}</div>', unsafe_allow_html=True)
    
    # PROBLEM SHEET: Native Markdown forces perfect mathematical equation parsing
    st.markdown(st.session_state.question_context)
    
    # Active Concept block
    st.markdown("""
    <div class="active-concept-section">
        <div class="active-concept-label">KEY CONCEPT</div>
        <div class="active-concept-desc">Apply Faraday's law of electromagnetic induction to find the maximum induced electromotive force in a rotating coil.</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Study Notebook Section (Pulled up under Key Concept)
    insight_count = len(st.session_state.insights)
    st.markdown(f"""
    <div class="notebook-header-row">
        <div class="notebook-title">Study Notebook</div>
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
                <div class="card-label" style="font-size: 0.64rem; font-weight:700; color:#86868B; text-transform:uppercase; letter-spacing: 0.04em;">{insight.get('theorem', 'Unlocked Step')}</div>
                <div class="card-value" style="font-family: monospace; font-size:1.1rem; margin-top:5px; color:#1D1D1F;">{insight.get('formula', '')}</div>
                <div style="font-size: 0.78rem; color: #86868B; margin-top: 6px;">Target value verified: {insight.get('result', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# COLUMN 3: MIDDLE GAP SPACE (10%)
# ==========================================
with col_space2:
    st.empty()


# ==========================================
# COLUMN 4: MINIMALIST PIXEL-PERFECT CHAT (20%)
# ==========================================
with col_chat:
    st.markdown('<div class="right-chat-panel">', unsafe_allow_html=True)
    
    # Header Info Block
    st.markdown('<div class="chat-mode-header">SOCRATES</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chat-mode-subheader">Active — {st.session_state.tutoring_mode}</div>', unsafe_allow_html=True)
    st.markdown('<div class="chat-header-divider"></div>', unsafe_allow_html=True)
    
    # Chat container
    chat_container = st.container(height=450, border=False)
    
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "assistant" or msg["role"] == "tutor":
                st.markdown(f"""
                <div class="msg-wrapper">
                    <div class="msg-sender-label-socrates">Socrates</div>
                    <div class="msg-socrates-card">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="msg-wrapper">
                    <div class="msg-sender-label-you">You</div>
                    <div class="msg-you-card">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            
    user_input = st.chat_input("Type your logic or formula...")
    
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with chat_container:
            st.markdown(f"""
            <div class="msg-wrapper">
                <div class="msg-sender-label-you">You</div>
                <div class="msg-you-card">{user_input}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Loader matching Image 2
            status_placeholder = st.markdown('<div class="status-indicator">Socrates is processing...</div>', unsafe_allow_html=True)
            
            try:
                base_url = BACKEND_URL.rstrip("/")
                response = requests.post(
                    f"{base_url}/chat/{st.session_state.session_id}",
                    json={"user_text": user_input},
                    timeout=15
                )
                status_placeholder.empty()
                
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
            <div class="msg-wrapper">
                <div class="msg-sender-label-socrates">Socrates</div>
                <div class="msg-socrates-card">{ai_response}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)
