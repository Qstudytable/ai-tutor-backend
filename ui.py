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
if "question_title" not in st.session_state:
    st.session_state.question_title = "Physics Dynamics Problem"
if "question_topic" not in st.session_state:
    st.session_state.question_topic = "Classical Mechanics"
if "tutoring_mode" not in st.session_state:
    st.session_state.tutoring_mode = "Active — Socratic Mode"


def extract_dynamic_metadata(data: dict):
    """Dynamically parses API payload or question markdown content to prevent topic mismatch."""
    topic = data.get("topic") or data.get("subject") or data.get("category")
    title = data.get("title") or data.get("question_name")
    
    # Fallback to smart parsing if API does not supply metadata keys
    if not topic:
        context_lower = st.session_state.question_context.lower()
        if "collides" in context_lower or "velocity" in context_lower or "mass" in context_lower:
            topic = "Classical Mechanics"
        elif "magnetic" in context_lower or "electromotive" in context_lower or "induction" in context_lower:
            topic = "Electromagnetism"
        else:
            topic = "General Physics"
            
    if not title:
        title = f"Problem Unit {st.session_state.current_question_id}"
        
    st.session_state.question_topic = topic
    st.session_state.question_title = title


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
            
            extract_dynamic_metadata(data)
        else:
            st.error(f"Failed to synchronize workspace state. Server returned code {res.status_code}.")
            st.stop()
    except Exception as e:
        st.error(f"Internal container sync failed: {e}")
        st.stop()


def init_session(q_id: str):
    """Initializes session on Port 8000. Safely handles container warmups."""
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
                
                extract_dynamic_metadata(data)
                return
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


def clean_html(html_str: str) -> str:
    """Removes leading spaces from all lines so markdown won't parse it as an indented code block."""
    return "\n".join(line.strip() for line in html_str.strip().split("\n"))


# --- EDITORIAL SYSTEM STYLING ---
st.markdown(textwrap.dedent("""
<style>
  /* Import Google Fonts directly */
  @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');

  /* Base premium minimalist setup - FORCED PURE WHITE GLOBALLY */
  html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, [data-testid="stVerticalBlock"] {
    background-color: #FFFFFF !important;
    color: #121212 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    -webkit-font-smoothing: antialiased;
  }
  
  /* Strip Streamlit system elements */
  header, footer, #MainMenu { display: none !important; }
  .block-container { padding: 0 !important; max-width: 100% !important; }

  /* Premium Header Navigation Bar */
  .top-header {
    background-color: #FFFFFF;
    border-bottom: 1px solid #EAE8E3;
    padding: 0 4%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 64px;
    width: 100%;
    box-sizing: border-box;
  }

  .brand {
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #121212;
  }

  .header-actions {
    display: flex;
    gap: 2rem;
    align-items: center;
  }

  .action-link {
    font-size: 11px;
    color: #5A5A57;
    text-decoration: none;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 500;
  }

  /* Custom flat link behavior for native Streamlit buttons */
  div.stButton > button {
    border: none !important;
    background-color: transparent !important;
    color: #5A5A57 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    padding: 0px !important;
    transition: color 0.2s ease;
    line-height: 1 !important;
    height: auto !important;
    white-space: nowrap !important;
    word-break: keep-all !important;
    width: 100% !important;
    min-width: unset !important;
  }
  div.stButton > button:hover {
    color: #121212 !important;
    background-color: transparent !important;
  }

  /* Target Streamlit Columns directly for perfect 7-60-8-25 container rendering */
  [data-testid="column"]:nth-of-type(1) {
    border-right: 1px solid #EAE8E3;
    height: calc(100vh - 64px);
    padding: 3rem 0.5rem !important;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background-color: #FFFFFF;
    overflow: hidden;
  }

  [data-testid="column"]:nth-of-type(2) {
    padding: 4rem 5% !important;
    overflow-y: auto !important;
    background-color: #FFFFFF;
    height: calc(100vh - 64px);
  }

  [data-testid="column"]:nth-of-type(3) {
    background-color: #FFFFFF;
    border-right: 1px solid #EAE8E3;
    height: calc(100vh - 64px);
  }

  [data-testid="column"]:nth-of-type(4) {
    padding: 2.5rem 1.75rem !important;
    background-color: #FFFFFF;
    height: calc(100vh - 64px);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  .sidebar-meta {
    font-size: 10px;
    color: #90908C;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    writing-mode: vertical-rl;
    transform: rotate(180deg);
    align-self: center;
    margin-bottom: auto;
  }

  .page-indicator {
    font-size: 11px;
    color: #5A5A57;
    text-align: center;
    margin-top: 1rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
  }

  .problem-meta {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #90908C;
    margin-bottom: 1.25rem;
  }

  .problem-title {
    font-family: 'EB Garamond', serif;
    font-size: 1.8rem;
    font-weight: 400;
    margin-bottom: 1.5rem;
    color: #121212;
    letter-spacing: -0.01em;
  }

  /* Protect KaTeX syntax from Garamond override */
  .stMarkdown p {
    font-family: 'EB Garamond', serif !important;
    font-size: 16px !important;
    line-height: 1.8 !important;
    color: #121212 !important;
  }
  .stMarkdown p .katex, .stMarkdown p .katex * {
    font-family: KaTeX_Main, 'Times New Roman', serif !important;
  }

  /* Study Notebook Elements */
  .notebook-wrapper {
    margin-top: 3rem;
    border-top: 1px solid #EAE8E3;
    padding-top: 2rem;
  }

  .notebook-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #5A5A57;
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
  }

  .notebook-canvas {
    background-color: #FFFFFF;
    border: 1.5px solid #121212 !important;
    border-radius: 6px;
    padding: 1.5rem 2rem;
    min-height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin-bottom: 1rem;
  }

  .notebook-placeholder-box {
    border: 1px solid #EAE8E3;
    border-radius: 6px;
    padding: 2.5rem 1.5rem;
    text-align: center;
    background-color: #FAFAF9;
  }

  .notebook-placeholder-text {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px;
    color: #5A5A57;
  }

  .notebook-formula {
    font-family: 'EB Garamond', serif;
    font-size: 18px;
    color: #121212;
    font-weight: 500;
    margin-bottom: 0.5rem;
  }

  .notebook-desc {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px;
    color: #5A5A57;
    line-height: 1.5;
  }

  .chat-title-area {
    margin-bottom: 1.5rem;
  }

  .chat-section-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #90908C;
  }

  /* Chat design configurations */
  .msg-wrapper {
    margin-bottom: 2rem;
    text-align: left;
  }

  .msg-sender-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #90908C;
    margin-bottom: 0.4rem;
  }

  .msg-content-text {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 13px;
    line-height: 1.6;
    color: #121212;
  }

  .msg-wrapper.system .msg-content-text {
    font-family: 'EB Garamond', serif !important;
    font-size: 14px !important;
    color: #121212 !important;
    border-left: 1.5px solid #121212;
    padding-left: 0.75rem;
    line-height: 1.6;
  }

  .status-indicator {
    font-family: 'EB Garamond', serif;
    font-style: italic;
    color: #5A5A57;
    font-size: 13px;
    margin-top: 1rem;
  }

  /* Override Streamlit chat formatting elements */
  div[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin-bottom: 1.5rem !important;
  }

  /* Flat bottom line input styling */
  [data-testid="stChatInput"] {
    border: none !important;
    border-bottom: 1.5px solid #121212 !important;
    border-radius: 0px !important;
    background: #FFFFFF !important;
    padding: 0.2rem 0rem !important;
  }

  /* Replace Streamlit default round submit icon with flat SEND label */
  button[data-testid="stChatInputSubmit"] {
    background: none !important;
    border: none !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: #121212 !important;
    width: auto !important;
    height: auto !important;
    padding: 0.5rem 0 0.5rem 1rem !important;
    transition: opacity 0.15s ease !important;
  }
  button[data-testid="stChatInputSubmit"]:hover {
    opacity: 0.7 !important;
  }
  button[data-testid="stChatInputSubmit"] svg {
    display: none !important;
  }
  button[data-testid="stChatInputSubmit"]::after {
    content: "SEND" !important;
    display: block !important;
  }
</style>
"""), unsafe_allow_html=True)


# --- THE COMPILER HEADER ---
st.markdown("""
<header class="top-header">
    <div class="brand">Socrates Workspace</div>
    <div class="header-actions">
        <a href="#" class="action-link">Index</a>
        <a href="#" class="action-link">Uploads</a>
        <a href="#" class="action-link">Exit Workspace</a>
    </div>
</header>
""", unsafe_allow_html=True)


# --- THE 7% / 60% / 8% / 25% HORIZONTAL MATRIX GRID ---
col_nav, col_workspace, col_spacer, col_chat = st.columns([0.07, 0.60, 0.08, 0.25])


# ==========================================
# COLUMN 1: NAVIGATION ASIDE (7% width)
# ==========================================
with col_nav:
    # Render the dynamic topic metadata in vertical-rl mode
    st.markdown(f'<div class="sidebar-meta">{st.session_state.question_topic}</div>', unsafe_allow_html=True)
    
    # Flat action navigators
    nav_link_col1, nav_link_col2 = st.columns([1, 1])
    with nav_link_col1:
        st.button("Prev", on_click=lambda: navigate("prev"))
    with nav_link_col2:
        st.button("Next", on_click=lambda: navigate("next"))
        
    st.markdown(f'<div class="page-indicator">ID {st.session_state.current_question_id}</div>', unsafe_allow_html=True)


# ==========================================
# COLUMN 2: PROBLEM WORKSPACE SHEET (60% width)
# ==========================================
with col_workspace:
    st.markdown(f'<div class="problem-meta">Problem Unit {st.session_state.current_question_id}</div>', unsafe_allow_html=True)
    st.markdown(f'<h1 class="problem-title">{st.session_state.question_title}</h1>', unsafe_allow_html=True)
    
    # Problem text output
    st.markdown(st.session_state.question_context)
    
    # Study Notebook dynamic compilation block
    insight_count = len(st.session_state.insights)
    notebook_html = f"""
    <div class="notebook-wrapper">
        <div class="notebook-label">
            <span>Active Study Notebook</span>
            <span>{insight_count} Unlocked Insights</span>
        </div>
    """
    
    if not st.session_state.insights:
        notebook_html += """
        <div class="notebook-placeholder-box">
            <div class="notebook-placeholder-text">No insights recorded yet. Solve steps in the chat to populate this area.</div>
        </div>
        """
    else:
        rendered_steps = set()
        for insight in st.session_state.insights:
            step_key = insight.get("step_key", "")
            if step_key in rendered_steps:
                continue
            rendered_steps.add(step_key)
            
            formula = insight.get('formula') or ""
            description = insight.get('description') or insight.get('desc') or f"Successfully verified: {insight.get('theorem', 'Concept')}. Calculated result quantity matches ground truth value: {insight.get('result', 'N/A')}."
            
            notebook_html += f"""
            <div class="notebook-canvas">
                <div class="notebook-formula">{formula}</div>
                <div class="notebook-desc">{description}</div>
            </div>
            """
    notebook_html += "</div>"
    
    # Output notebook cleanly without leading spaces
    st.markdown(clean_html(notebook_html), unsafe_allow_html=True)


# ==========================================
# COLUMN 3: STRUCTURAL SEPARATOR GUTTER (8% width)
# ==========================================
with col_spacer:
    pass


# ==========================================
# COLUMN 4: SOCRATIC SIDEBAR DIALOGUE (25% width)
# ==========================================
with col_chat:
    st.markdown('<div class="chat-title-area"><span class="chat-section-label">Dialogue Assistant</span></div>', unsafe_allow_html=True)
    
    # Height-locked conversational viewport
    chat_container = st.container(height=450, border=False)
    
    with chat_container:
        for msg in st.session_state.chat_history:
            sender = "Socrates" if msg["role"] in ["assistant", "tutor"] else "You"
            wrapper_class = "msg-wrapper system" if sender == "Socrates" else "msg-wrapper"
            st.markdown(f"""
            <div class="{wrapper_class}">
                <div class="msg-sender-label">{sender}</div>
                <div class="msg-content-text">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
            
    # Minimal Chat Input pinned at the base
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
                    st.session_state.tutoring_mode = "Active — Socratic Mode" if backend_mode == "SOCRATIC" else "Active — Direct Mode"
                    
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
