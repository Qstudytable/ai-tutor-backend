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
    st.session_state.tutoring_mode = "SOCRATIC MODE"


def sync_session_snapshot(session_id: str):
    """Syncs session state. Fails loudly if backend is unreachable."""
    try:
        base_url = BACKEND_URL.rstrip("/")
        res = requests.get(f"{base_url}/session/{session_id}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.session_state.chat_history = data.get("chat_history") or []
            st.session_state.insights = data.get("notebook_history") or []
            mode = data.get("tutoring_mode", "socratic")
            st.session_state.tutoring_mode = "SOCRATIC MODE" if mode == "socratic" else "DIRECT MODE"
        else:
            st.error(f"Failed to synchronize workspace state. Server returned code {res.status_code}.")
            st.stop()
    except Exception as e:
        st.error(f"Internal container sync failed: {e}")
        st.stop()


def init_session(q_id: str):
    """
    Initializes session on Port 8000.
    Retries automatically to handle backend startup delays while Uvicorn caches questions.
    """
    base_url = BACKEND_URL.rstrip("/")
    url = f"{base_url}/session/start/{q_id.strip()}"
    
    max_retries = 5
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
                st.session_state.tutoring_mode = "SOCRATIC MODE"
                return  # Connection successful, exit function
            else:
                st.error(f"Internal initialization failed (Status {res.status_code}).")
                st.stop()
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                st.warning(f"Connecting to physics tutor engine... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                st.error("Error: Could not spin up the physics tutor state engine on GCP.")
                st.info("The server is online, but the database backend failed to wake up in time. Please reload.")
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
    border-bottom: 1px solid #F0F0F2;
    padding-bottom: 0.5rem;
    margin-bottom: 2rem;
    padding-left: 7%;
    padding-right: 20%;
  }

  .top-bar-title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #1D1D1F;
    margin-top: 6px;
  }

  .top-bar-center {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1.5rem;
  }

  .problem-indicator {
    font-family: Georgia, "Times New Roman", serif;
    font-style: italic;
    font-size: 0.9rem;
    border-bottom: 1px solid #1D1D1F;
    color: #1D1D1F;
    padding-bottom: 2px;
  }

  .top-bar-date {
    font-size: 0.72rem;
    font-weight: 500;
    color: #86868B;
    letter-spacing: 0.05em;
    text-align: right;
    margin-top: 6px;
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

  /* Override Streamlit Chat layout elements to strip bubbles */
  div[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin-bottom: 1.5rem !important;
  }

  /* Flat, un-bordered navigation button styling */
  div.stButton > button {
    border: none !important;
    background-color: transparent !important;
    color: #86868B !important;
    font-family: -apple-system, sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 0px !important;
    transition: color 0.2s ease;
  }
  div.stButton > button:hover {
    color: #1D1D1F !important;
    background-color: transparent !important;
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


# --- VI. NATIVE EDITORIAL HEADER WITH WORKSPACE NAVIGATION ---
st.markdown('<div class="top-bar-container">', unsafe_allow_html=True)
h_col_left, h_col_center, h_col_right = st.columns([2, 5, 2])

with h_col_left:
    st.markdown('<div class="top-bar-title">PHYSICS TUTOR</div>', unsafe_allow_html=True)

with h_col_center:
    # Renders active navigation links matching your target layout
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
    time_str = dt.now().strftime("%b %d · %I:%M %p").upper()
    st.markdown(f'<div class="top-bar-date">{time_str}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# --- VII. EXACT HORIZONTAL GRID LAYOUT ---
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
        rendered_steps = set()
        for insight in st.session_state.insights:
            step_key = insight.get("step_key", "")
            # Skip if we already displayed this card in this view cycle
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
