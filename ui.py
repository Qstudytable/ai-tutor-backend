import streamlit as st
import requests
import time
from datetime import datetime as dt
import textwrap

# --- GLOBAL LAYOUT CONFIGURATION ---
st.set_page_config(
    layout="wide", 
    initial_sidebar_state="collapsed", 
    page_title="STUDYtable"
)

# SINGLE-CONTAINER ROUTING
BACKEND_URL = "http://127.0.0.1:8000"

# --- 1. STATE MANAGEMENT & RECOVERY ---
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "current_question_id" not in st.session_state:
    st.session_state.current_question_id = "00899"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "How can I help?"}
    ]
if "insights" not in st.session_state:
    st.session_state.insights = []
if "question_context" not in st.session_state:
    st.session_state.question_context = ""
if "tutoring_mode" not in st.session_state:
    st.session_state.tutoring_mode = "Active — Socratic Mode"


# --- 2. RECOVERY WORKSPACE FUNCTIONS ---
def sync_session_snapshot(session_id: str):
    """Syncs session state dynamically from backend when requested."""
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


def init_session(q_id: str, retain_history: bool = False):
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
                
                if not retain_history:
                    st.session_state.chat_history = [
                        {"role": "assistant", "content": "Welcome to the workspace. Let's step through this physics problem together. How can I help you resolve the active step?"}
                    ]
                    st.session_state.insights = []
                st.session_state.tutoring_mode = "Active — Socratic Mode"
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


# --- 3. DYNAMIC BACKEND NAVIGATION ---
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


# --- 4. INTERCEPT INTERACTIVE ACTIONS ---
if "nav_action" in st.query_params:
    action = st.query_params["nav_action"]
    st.query_params.clear()  
    navigate(action)


# --- 5. INITIALIZATION RUNNER DEPLOYMENT ---
if st.session_state.session_id is None:
    init_session(st.session_state.current_question_id)


# --- 6. EDITORIAL SYSTEM STYLING ---
st.markdown(textwrap.dedent("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');

  html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, [data-testid="stVerticalBlock"] {
    background-color: #FFFFFF !important;
    color: #121212 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    -webkit-font-smoothing: antialiased;
  }
  
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

  /* Structural Columns Layout Setup */
  [data-testid="column"]:nth-of-type(1) {
    border-right: 1px solid #EAE8E3;
    height: calc(100vh - 64px);
    padding: 3rem 1.5rem !important;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background-color: #FFFFFF;
  }

  [data-testid="column"]:nth-of-type(2) {
    padding: 4rem 6% !important;
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
    overflow-y: auto !important;
  }

  .page-indicator {
    font-size: 12px;
    color: #5A5A57;
    text-align: center;
  }

  .problem-meta {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #90908C;
    margin-bottom: 1.25rem;
  }

  /* Standardized entry wrapper rule for complex mixed markdown states */
  .problem-context-wrapper .stMarkdown p {
    font-family: 'EB Garamond', serif !important;
    font-size: 16px !important;
    line-height: 1.8 !important;
    color: #121212 !important;
  }
  
  .stMarkdown p .katex, .stMarkdown p .katex * {
    font-family: KaTeX_Main, 'Times New Roman', serif !important;
  }

  /* Notebook Design Layout */
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

  /* Native Chat Structure Overrides */
  div[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin-bottom: 2rem !important;
  }
  
  /* Hide the default chat avatars */
  div[data-testid="stChatMessage"] div[data-testid="stChatMessageAvatar"] {
    display: none !important;
  }
  
  /* Reset standard padding on message layout boxes */
  div[data-testid="stChatMessage"] div.stMarkdown {
    padding: 0 !important;
  }

  /* Universal typographic styles for assistant vs user blocks */
  div[data-testid="stChatMessage"] p {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 13px !important;
    line-height: 1.6 !important;
    color: #121212 !important;
  }

  /* Specific left-accent styling for Socrates messages */
  div[data-testid="stChatMessageContent"]:has(div.socrates-marker) p {
    font-family: 'EB Garamond', serif !important;
    font-size: 15px !important;
    color: #121212 !important;
    line-height: 1.6 !important;
  }
  
  div[data-testid="stChatMessageContent"]:has(div.socrates-marker) div.stMarkdown {
    border-left: 1.5px solid #121212;
    padding-left: 0.75rem !important;
  }

  .custom-sender-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #90908C;
    margin-bottom: 0.4rem;
  }

  /* Counteract Streamlit's fixed-to-viewport default chat layout styling rules */
  div[data-testid="stChatInputContainer"] {
    background-color: transparent !important;
    padding: 0px !important;
    border: none !important;
    position: static !important;
    width: 100% !important;
  }

  [data-testid="stChatInput"] {
    border: none !important;
    border-bottom: 1.5px solid #121212 !important;
    border-radius: 0px !important;
    background: #FFFFFF !important;
    padding: 0.2rem 0rem !important;
  }

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
  button[data-testid="stChatInputSubmit"]:hover { opacity: 0.7 !important; }
  button[data-testid="stChatInputSubmit"] svg { display: none !important; }
  button[data-testid="stChatInputSubmit"]::after { content: "SEND" !important; display: block !important; }
  
  /* Standardize padding properties for inner spinner frames */
  div[data-testid="stSpinner"] {
    padding: 0px !important;
    margin-bottom: 1rem !important;
  }
</style>
"""), unsafe_allow_html=True)


# --- 7. HEADER COMPILATION ---
st.markdown("""
<header class="top-header">
    <div style="display: flex; align-items: center; gap: 40px;">
        <div class="brand">Socrates Workspace</div>
        <div style="display: flex; gap: 16px; align-items: center;">
            <a href="?nav_action=prev" target="_self" style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 11px; font-weight: 500; color: #5A5A57; text-decoration: none; text-transform: uppercase; letter-spacing: 0.08em;">Prev</a>
            <a href="?nav_action=next" target="_self" style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 11px; font-weight: 500; color: #5A5A57; text-decoration: none; text-transform: uppercase; letter-spacing: 0.08em;">Next</a>
        </div>
    </div>
    <div class="header-actions">
        <a href="#" class="action-link">Index</a>
        <a href="#" class="action-link">Uploads</a>
        <a href="#" class="action-link">Exit Workspace</a>
    </div>
</header>
""", unsafe_allow_html=True)


# --- 8. SYSTEM HORIZONTAL MATRIX GRID ---
col_nav, col_workspace, col_spacer, col_chat = st.columns([0.09, 0.60, 0.06, 0.25])

# COLUMN 1: NAVIGATION ASIDE
with col_nav:
    indicator_digit = st.session_state.current_question_id[-1]
    page_num = indicator_digit if indicator_digit.isdigit() else "1"
    st.markdown(f'<div class="page-indicator">0{page_num}/04</div>', unsafe_allow_html=True)

# COLUMN 2: PROBLEM WORKSPACE SHEET
with col_workspace:
    st.markdown(f'<div class="problem-meta">Problem Unit {st.session_state.current_question_id}</div>', unsafe_allow_html=True)
    
    # Enclosing dynamic markdown in explicit contextual containers to isolate theme injections
    st.markdown(f'<div class="problem-context-wrapper">', unsafe_allow_html=True)
    st.markdown(st.session_state.question_context)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Render Insights Notebook
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
            notebook_html += f"""
            <div class="notebook-canvas">
                <div class="notebook-formula">{insight.get('formula', '')}</div>
                <div class="notebook-desc">Successfully verified: {insight.get('theorem', 'Concept')}. Calculated result quantity matches ground truth value: {insight.get('result', 'N/A')}.</div>
            </div>
            """
    notebook_html += "</div>"
    st.markdown(notebook_html, unsafe_allow_html=True)

# COLUMN 3: STRUCTURAL GUTTER SEPARATOR
with col_spacer:
    pass

# COLUMN 4: SOCRATIC SIDEBAR DIALOGUE
with col_chat:
    st.markdown('<div class="chat-title-area"><span class="chat-section-label">Dialogue Assistant</span></div>', unsafe_allow_html=True)
    
    chat_container = st.container(height=520, border=False)
    
    # Display dialogue history upfront via native containers
    with chat_container:
        for msg in st.session_state.chat_history:
            is_assistant = msg["role"] in ["assistant", "tutor"]
            sender_title = "Socrates" if is_assistant else "You"
            
            # The CSS relies on this wrapper tag for contextual target rendering
            marker = '<div class="socrates-marker"></div>' if is_assistant else ""
            
            with st.chat_message(msg["role"]):
                st.markdown(f'<div class="custom-sender-label">{sender_title}</div>{marker}', unsafe_allow_html=True)
                st.markdown(msg["content"])

    user_input = st.chat_input("Ask a question...")
    
    if user_input:
        # 1. Immediately append and visually render user's message inside the column log
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with chat_container:
            with st.chat_message("user"):
                st.markdown('<div class="custom-sender-label">You</div>', unsafe_allow_html=True)
                st.markdown(user_input)
        
        # 2. Run the loader inline where the assistant's message frame will land
        with chat_container:
            with st.chat_message("assistant"):
                st.markdown('<div class="custom-sender-label">Socrates</div><div class="socrates-marker"></div>', unsafe_allow_html=True)
                
                with st.spinner("Socrates is analyzing..."):
                    try:
                        base_url = BACKEND_URL.rstrip("/")
                        response = requests.post(
                            f"{base_url}/chat/{st.session_state.session_id}",
                            json={"user_text": user_input},
                            timeout=15
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            ai_response = data.get("ai_response", "I'm having trouble analyzing this step.")
                            backend_mode = data.get("phase", "SOCRATIC")
                            st.session_state.tutoring_mode = "Active — Socratic Mode" if backend_mode == "SOCRATIC" else "Active — Direct Mode"
                            
                            nb_updates = data.get("notebook_updates", {})
                            if nb_updates and nb_updates.get("official_solution"):
                                st.session_state.insights.append(nb_updates["official_solution"])
                        
                        elif response.status_code in [404, 500]:
                            init_session(st.session_state.current_question_id, retain_history=True)
                            ai_response = "Workspace sync was interrupted. Your session state has been restored—please resubmit your formula."
                        else:
                            ai_response = f"GCP Engine Error: code {response.status_code}."
                            
                    except Exception as e:
                        ai_response = "GCP Synchronizer Error: unable to connect to API gateway."
                
                # Render the final text inside the open message layout box (allows native LaTeX conversion)
                st.markdown(ai_response)
        
        # 3. Save assistant message to state history and execute exactly one single clean app sync
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        st.rerun()
