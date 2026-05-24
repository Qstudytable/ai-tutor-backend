import streamlit as st
import requests
from datetime import datetime as dt
import textwrap

# --- GLOBAL LAYOUT CONFIGURATION ---
st.set_page_config(
    layout="wide", 
    initial_sidebar_state="collapsed", 
    page_title="Physics Tutor"
)

# Connects directly to your live GCP backend API gateway
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
    st.session_state.tutoring_mode = "SOCRATIC MODE"


def sync_session_snapshot(session_id: str):
    """Syncs state dynamically from MongoDB if the browser is refreshed."""
    try:
        res = requests.get(f"{BACKEND_URL}/session/{session_id}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.session_state.chat_history = data.get("chat_history") or []
            st.session_state.insights = data.get("notebook_history") or []
            mode = data.get("tutoring_mode", "socratic")
            st.session_state.tutoring_mode = "SOCRATIC MODE" if mode == "socratic" else "DIRECT MODE"
        else:
            st.error(f"Sync Failure: Backend returned status code {res.status_code}.")
            st.stop()
    except Exception as e:
        st.error(f"State synchronization failed. Cannot reach tutor API: {e}")
        st.stop()


def init_session(q_id: str):
    """Initializes a new attempt-based tracking session on GCP."""
    try:
        res = requests.post(f"{BACKEND_URL}/session/start/{q_id}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.session_state.session_id = data.get("session_id")
            st.session_state.current_question_id = data.get("question_id")
            st.session_state.question_context = data.get("context")
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Welcome to the workspace. Let's step through this physics problem together. How can I help you resolve the active step?"}
            ]
            st.session_state.insights = []
            st.session_state.tutoring_mode = "SOCRATIC MODE"
        else:
            st.error(f"Initialization Failed: Backend returned status code {res.status_code}.")
            st.stop()
    except Exception as e:
        st.error(f"Could not connect to live GCP Tutor Engine: {e}")
        st.stop()


def navigate(direction: str):
    """Queries backend navigation routing to step through playlist cleanly."""
    try:
        res = requests.get(f"{BACKEND_URL}/questions/navigate/{st.session_state.current_question_id}/{direction}", timeout=5)
        if res.status_code == 200:
            next_q_id = res.json().get("question_id")
            if next_q_id:
                init_session(next_q_id)
        else:
            st.error(f"Navigation error: API returned {res.status_code}")
    except Exception as e:
        st.error(f"Could not reach navigation endpoint: {e}")


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

  /* Premium Top Navigation Bar */
  .top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #F0F0F2;
    padding-bottom: 0.8rem;
    margin-bottom: 2rem;
    margin-left: 7%;
    margin-right: 20%;
  }
  .top-bar-title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #1D1D1F;
  }
  .top-bar-date {
    font-size: 0.72rem;
    font-weight: 500;
    color: #86868B;
    letter-spacing: 0.05em;
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
    font-size: 1.6rem; 
    font-weight: 600; 
    letter-spacing: -0.01em; 
    color: #1D1D1F; 
    margin-bottom: 1.5rem; 
  }
  
  /* CRITICAL FIX: Forces markdown text to style as Georgia serif, preserving LaTeX math parsing */
  .stMarkdown p {
    font-family: Georgia, "Times New Roman", Times, serif !important;
    font-size: 1.15rem !important;
    line-height: 1.8 !important;
    color: #1D1D1F !important;
  }
  
  /* Active Concept metadata box with a left vertical border line */
  .active-concept-section {
    border-left: 1px solid #1D1D1F;
    padding-left: 1.2rem;
    margin: 2.2rem 0;
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
    margin-top: 2.5rem;
    border-bottom: 1px solid #F0F0F2;
    padding-bottom: 0.5rem;
  }
  .notebook-title {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #1D1D1F;
  }
  .notebook-count {
    font-size: 0.68rem;
    color: #86868B;
  }
  .notebook-container {
    border: 1px solid #E5E5EA;
    border-radius: 4px;
    padding: 5rem 1.5rem;
    background-color: #FFFFFF;
    text-align: center;
    min-height: 250px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .notebook-placeholder {
    font-family: Georgia, "Times New Roman", serif;
    font-style: italic;
    color: #86868B;
    font-size: 0.98rem;
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
    padding-left: 1.8rem;
    min-height: 75vh;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  
  .chat-mode-header {
    text-align: center;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: #86868B;
    text-transform: uppercase;
    margin-bottom: 1.8rem;
  }

  /* Unbubbled typography chat wrapper */
  .msg-wrapper {
    margin-bottom: 1.5rem;
  }
  .msg-sender {
    font-size: 0.72rem;
    font-weight: 700;
    color: #1D1D1F;
    margin-bottom: 0.3rem;
    letter-spacing: 0.02em;
  }
  .msg-content {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    font-size: 0.92rem;
    line-height: 1.6;
    color: #1D1D1F;
  }
  .status-indicator {
    font-family: Georgia, "Times New Roman", serif;
    font-style: italic;
    color: #86868B;
    font-size: 0.88rem;
    margin-top: 1rem;
  }

  /* Override Streamlit Chat layout elements */
  div[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin-bottom: 1.5rem !important;
  }
  
  /* Rounded navigation buttons */
  [data-testid="stButton"] button {
    border-radius: 24px;
    border: 1px solid #E5E5EA;
    background: #FFFFFF;
    color: #1D1D1F;
    font-weight: 500;
    font-size: 0.8rem;
    padding: 0.2rem 1rem;
  }
  [data-testid="stButton"] button:hover {
    background: #F5F5F7;
    border-color: #D2D2D7;
  }
  
  /* Clean editorial input overrides */
  [data-testid="stChatInput"] {
    border: 1px solid #E5E5EA !important;
    border-radius: 4px !important;
    background: #FFFFFF !important;
    padding: 0.2rem !important;
  }
</style>
"""), unsafe_allow_html=True)


# --- IV. TOP BAR NAVIGATION ---
time_str = dt.now().strftime("%b %d · %I:%M %p").upper()
st.markdown(f"""
<div class="top-bar">
    <div class="top-bar-title">Physics Tutor</div>
    <div class="top-bar-date">{time_str}</div>
</div>
""", unsafe_allow_html=True)


# --- V. EXACT RATIOMETRIC GRID LAYOUT ---
# 7% Space | 65% Workspace | 8% Space | 20% Tutor Chat
col_space1, col_workspace, col_space2, col_chat = st.columns([0.07, 0.65, 0.08, 0.20])


# ==========================================
# COLUMN 1: LEFT BREATHING MARGIN (7%)
# ==========================================
with col_space1:
    st.empty()


# ==========================================
# COLUMN 2: WORKSPACE CONTAINER (65%)
# ==========================================
with col_workspace:
    st.markdown('<div class="tag">Class 12 · Electromagnetic Induction</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="title">Problem {st.session_state.current_question_id}</div>', unsafe_allow_html=True)
    
    # PROBLEM SHEET: Rendered natively to keep KaTeX engine parsing LaTeX math beautifully
    st.markdown(st.session_state.question_context)
    
    # Active Concept block
    st.markdown("""
    <div class="active-concept-section">
        <div class="active-concept-label">Active Concept</div>
        <div class="active-concept-desc">Apply Faraday's law of electromagnetic induction to find the maximum induced electromotive force in a rotating coil.</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Study Notebook Header Row
    insight_count = len(st.session_state.insights)
    st.markdown(f"""
    <div class="notebook-header-row">
        <div class="notebook-title">Study Notebook</div>
        <div class="notebook-count">{insight_count} Insights Unlocked</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Study Notebook content card
    if not st.session_state.insights:
        st.markdown("""
        <div class="notebook-container">
            <div class="notebook-placeholder">Awaiting formulas and insights from chat...</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for insight in st.session_state.insights:
            st.markdown(f"""
            <div class="notebook-card">
                <div class="card-label" style="font-size: 0.64rem; font-weight:700; color:#86868B; text-transform:uppercase; letter-spacing: 0.04em;">{insight.get('theorem', 'Unlocked Step')}</div>
                <div class="card-value" style="font-family: monospace; font-size:1.1rem; margin-top:5px; color:#1D1D1F;">{insight.get('formula', '')}</div>
                <div style="font-size: 0.78rem; color: #86868B; margin-top: 6px;">Target value verified: {insight.get('result', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# COLUMN 3: MIDDLE BREATHING MARGIN (8%)
# ==========================================
with col_space2:
    st.empty()


# ==========================================
# COLUMN 4: MINIMALIST AI TUTOR CHAT (20%)
# ==========================================
with col_chat:
    # Editorial wrapper for the chat column
    st.markdown(f'<div class="chat-mode-header">{st.session_state.tutoring_mode}</div>', unsafe_allow_html=True)
    
    # Clean dialogue container
    chat_container = st.container(height=450, border=False)
    
    with chat_container:
        for msg in st.session_state.chat_history:
            sender = "Socrates" if msg["role"] == "assistant" or msg["role"] == "tutor" else "You"
            st.markdown(f"""
            <div class="msg-wrapper">
                <div class="msg-sender">{sender}</div>
                <div class="msg-content">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
            
    # Minimal Chat Input pinned at the base
    user_input = st.chat_input("Type logic or formula...")
    
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with chat_container:
            st.markdown(f"""
            <div class="msg-wrapper">
                <div class="msg-sender">You</div>
                <div class="msg-content">{user_input}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Subtle loading text during API request lifecycle
            status_placeholder = st.markdown('<div class="status-indicator">Analyzing physics principles...</div>', unsafe_allow_html=True)
            
            try:
                response = requests.post(
                    f"{BACKEND_URL}/chat/{st.session_state.session_id}",
                    json={"user_text": user_input},
                    timeout=15
                )
                status_placeholder.empty() # Remove loader smoothly
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("ai_response", "I'm having trouble analyzing this step.")
                    
                    backend_mode = data.get("phase", "SOCRATIC")
                    st.session_state.tutoring_mode = "SOCRATIC MODE" if backend_mode == "SOCRATIC" else "DIRECT MODE"
                    
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
                <div class="msg-sender">Socrates</div>
                <div class="msg-content">{ai_response}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        st.rerun()
