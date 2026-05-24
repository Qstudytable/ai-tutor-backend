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

BACKEND_URL = "http://127.0.0.1:8000"
MVP_QUESTIONS = ["00899", "00900", "00901"]

# --- STATE MANAGEMENT & RECOVERY ---
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "current_question_id" not in st.session_state:
    st.session_state.current_question_id = MVP_QUESTIONS[st.session_state.q_index]
if "session_id" not in st.session_state:
    st.session_state.session_id = None
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

# Sync session details from backend snapshot
def sync_session_snapshot(session_id: str):
    try:
        res = requests.get(f"{BACKEND_URL}/session/{session_id}", timeout=3)
        if res.status_code == 200:
            data = res.json()
            st.session_state.chat_history = data.get("chat_history") or []
            st.session_state.insights = data.get("notebook_history") or []
            mode = data.get("tutoring_mode", "socratic")
            st.session_state.tutoring_mode = "Socratic Mode" if mode == "socratic" else "Direct Mode"
    except Exception:
        pass

# Initialize session
def init_session(q_id: str):
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
            st.session_state.tutoring_mode = "Socratic Mode"
    except Exception:
        # Editorial simulation fallback
        st.session_state.session_id = f"demo_fallback_{q_id}"
        st.session_state.current_question_id = q_id
        st.session_state.question_context = (
            "A rectangular coil has $N = 100$ turns, with side lengths $ab = 30\\text{cm}$ and $ad = 20\\text{cm}$. "
            "It is placed in a uniform magnetic field with a magnetic induction strength of $B = 0.8\\text{T}$. "
            "The coil rotates uniformly about the axis O' starting from the position shown in the diagram, "
            "with an angular velocity of $\\omega = 100\\pi$ rad/s."
        )
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Welcome to the workspace. Let's step through this physics problem together. How can I help you resolve the active step?"}
        ]
        st.session_state.insights = []

if st.session_state.session_id is None:
    init_session(st.session_state.current_question_id)
else:
    if not st.session_state.session_id.startswith("demo_fallback_"):
        sync_session_snapshot(st.session_state.session_id)


# --- EDITORIAL MINIMALIST CSS ARCHITECTURE ---
st.markdown(textwrap.dedent("""
<style>
  /* Base editorial typography settings */
  html, body, [data-testid="stAppViewContainer"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: #FFFFFF;
    color: #1D1D1F;
  }
  
  /* Hide standard Streamlit elements */
  header, footer, #MainMenu { display: none !important; }
  .block-container { padding: 1.5rem 4rem !important; max-width: 100% !important; }

  /* Top Bar Separator Styling */
  .top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #E5E5EA;
    padding-bottom: 0.8rem;
    margin-bottom: 2rem;
  }
  .top-bar-title {
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #1D1D1F;
  }
  .top-bar-date {
    font-size: 0.75rem;
    font-weight: 500;
    color: #86868B;
    letter-spacing: 0.05em;
  }

  /* Editorial Left Column Layout */
  .tag { font-size: 0.72rem; font-weight: 600; color: #86868B; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 1rem; }
  .title { font-size: 1.8rem; font-weight: 600; letter-spacing: -0.01em; color: #1D1D1F; margin-bottom: 1.5rem; }
  
  /* High readability editorial font for mathematical word problems */
  .problem-text {
    font-family: Georgia, "Times New Roman", Times, serif;
    font-size: 1.22rem;
    line-height: 1.8;
    color: #1D1D1F;
    margin-bottom: 2rem;
  }
  
  /* Active Concept Card */
  .active-concept-section {
    border-left: 2px solid #1D1D1F;
    padding-left: 1.2rem;
    margin: 2.5rem 0;
  }
  .active-concept-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: #86868B;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
  }
  .active-concept-desc {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 1.08rem;
    line-height: 1.6;
    color: #1D1D1F;
  }

  /* Study Notebook empty/filled states */
  .notebook-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    margin-top: 2rem;
  }
  .notebook-title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #1D1D1F;
  }
  .notebook-count {
    font-size: 0.72rem;
    color: #86868B;
  }
  .notebook-container {
    border: 1px solid #E5E5EA;
    border-radius: 8px;
    padding: 3rem 1.5rem;
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
    font-size: 1.05rem;
  }
  .notebook-card {
    border: 1px solid #E5E5EA;
    border-radius: 6px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    text-align: left;
    background-color: #FFFFFF;
  }

  /* Minimalist Chat Right Column divider */
  .right-chat-panel {
    border-left: 1px solid #E5E5EA;
    padding-left: 2.5rem;
    height: 80vh;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  
  /* Chat Header Mode Label */
  .chat-mode-header {
    text-align: center;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #86868B;
    text-transform: uppercase;
    margin-bottom: 2rem;
  }

  /* Minimal Text Messages without Bubbles */
  .msg-wrapper {
    margin-bottom: 1.8rem;
  }
  .msg-sender {
    font-size: 0.78rem;
    font-weight: 700;
    color: #1D1D1F;
    margin-bottom: 0.4rem;
  }
  .msg-content {
    font-size: 0.96rem;
    line-height: 1.6;
    color: #1D1D1F;
  }
  .status-indicator {
    font-family: Georgia, "Times New Roman", serif;
    font-style: italic;
    color: #86868B;
    font-size: 0.92rem;
    margin-top: 1rem;
  }

  /* Target Streamlit native chat elements to match minimal typography */
  div[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin-bottom: 1.8rem !important;
  }
  div[data-testid="stChatMessageHeader"] {
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    color: #1D1D1F !important;
    margin-bottom: 0.4rem !important;
    text-transform: capitalize;
  }
  
  /* Inline minimalist input overrides */
  [data-testid="stChatInput"] {
    border: 1px solid #E5E5EA !important;
    border-radius: 8px !important;
    background: #FFFFFF !important;
    padding: 0.3rem !important;
  }
</style>
"""), unsafe_allow_html=True)


# --- I. EDITORIAL HEADER ---
time_str = dt.now().strftime("%b %d · %I:%M %p").upper()
st.markdown(f"""
<div class="top-bar">
    <div class="top-bar-title">Physics Tutor</div>
    <div class="top-bar-date">{time_str}</div>
</div>
""", unsafe_allow_html=True)


# --- II. WORKSPACE GRID SPLIT ---
left_col, right_col = st.columns([5.8, 4.2], gap="large")

# ==========================================
# LEFT PANEL: THE PHYSICS PROBLEM SHEET
# ==========================================
with left_col:
    st.markdown('<div class="tag">Class 12 · Electromagnetic Induction</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="title">Problem {st.session_state.current_question_id}</div>', unsafe_allow_html=True)
    
    # Beautiful serif problem description
    st.markdown(f'<div class="problem-text">{st.session_state.question_context}</div>', unsafe_allow_html=True)
    
    # Elegant Active Concept Card
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
        <div class="notebook-count">{insight_count} Insights Recorded</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Notebook Dynamic Rendering
    if not st.session_state.insights:
        st.markdown("""
        <div class="notebook-container">
            <div class="notebook-placeholder">Awaiting formulas and insights from chat...</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Unlocked insights render cleanly in structured editorial blocks
        for insight in st.session_state.insights:
            st.markdown(f"""
            <div class="notebook-card">
                <div class="card-label" style="font-size: 0.68rem; font-weight:700; color:#86868B; text-transform:uppercase;">{insight.get('theorem', 'Unlocked Step')}</div>
                <div class="card-value" style="font-family: monospace; font-size:1.1rem; margin-top:5px; color:#1D1D1F;">{insight.get('formula', '')}</div>
                <div style="font-size: 0.8rem; color: #86868B; margin-top: 6px;">Target value verified: {insight.get('result', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# RIGHT PANEL: MINIMAL TUTOR INTERACTION
# ==========================================
with right_col:
    # We wrap in a visual spacer panel to apply left divider styling
    st.markdown(f'<div class="chat-mode-header">{st.session_state.tutoring_mode}</div>', unsafe_allow_html=True)
    
    # Scrollable native clean list container
    chat_container = st.container(height=480, border=False)
    
    with chat_container:
        for msg in st.session_state.chat_history:
            sender = "Socrates" if msg["role"] == "assistant" else "You"
            
            # Render un-bubbled editorial message format
            st.markdown(f"""
            <div class="msg-wrapper">
                <div class="msg-sender">{sender}</div>
                <div class="msg-content">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
            
    # Minimal Chat Input pinned beautifully at the bottom
    user_input = st.chat_input("Type logic or formula...")
    
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Display the user's text immediately
        with chat_container:
            st.markdown(f"""
            <div class="msg-wrapper">
                <div class="msg-sender">You</div>
                <div class="msg-content">{user_input}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Beautiful editorial status text during request lifecycle
            status_placeholder = st.markdown('<div class="status-indicator">Analyzing physics principles...</div>', unsafe_allow_html=True)
            
            try:
                response = requests.post(
                    f"{BACKEND_URL}/chat/{st.session_state.session_id}",
                    json={"user_text": user_input},
                    timeout=15
                )
                status_placeholder.empty() # Remove loader status smoothly
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("ai_response", "I'm having trouble analyzing this step.")
                    
                    # Update tutoring mode display dynamically if it changes
                    backend_mode = data.get("phase", "SOCRATIC")
                    st.session_state.tutoring_mode = "Socratic Mode" if backend_mode == "SOCRATIC" else "Direct Mode"
                    
                    nb_updates = data.get("notebook_updates", {})
                    if nb_updates and nb_updates.get("official_solution"):
                        st.session_state.insights.append(nb_updates["official_solution"])
                else:
                    ai_response = "System error: Feedback loop disrupted."
            except Exception:
                status_placeholder.empty()
                ai_response = "API synchronization in progress. Please hold."
            
            # Print Socrates' reply
            st.markdown(f"""
            <div class="msg-wrapper">
                <div class="msg-sender">Socrates</div>
                <div class="msg-content">{ai_response}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        st.rerun()
