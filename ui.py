import streamlit as st
import requests
import datetime
from datetime import datetime as dt

# Set page config for wide layout and clean default elements
st.set_page_config(
    page_title="Physics Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for high-fidelity matching of colors, typography, and layout spacing
st.markdown("""
  <style>
    /* Global styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Lora:ital,wght@0,400;0,500;1,400&display=swap');
     
    html, body, [data-testid="stAppViewContainer"] {
      background-color: #FFFFFF;
      font-family: 'Inter', -apple-system, sans-serif;
      color: #0F172A;
    }
     
    /* Remove default Streamlit top decoration and padding */
    [data-testid="stHeader"] {
      display: none;
    }
    .block-container {
      padding-top: 1.5rem !important;
      padding-bottom: 1.5rem !important;
      padding-left: 3rem !important;
      padding-right: 3rem !important;
    }
     
    /* Header styling */
    .header-container {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #E2E8F0;
      padding-bottom: 1rem;
      margin-bottom: 2rem;
    }
    .header-title {
      font-family: 'Inter', sans-serif;
      font-weight: 700;
      font-size: 0.9rem;
      letter-spacing: 0.15em;
      color: #0F172A;
    }
    .header-date {
      font-family: 'Inter', sans-serif;
      font-size: 0.75rem;
      color: #64748B;
      letter-spacing: 0.05em;
    }
     
    /* Breadcrumb */
    .breadcrumb {
      font-family: 'Inter', sans-serif;
      font-size: 0.7rem;
      font-weight: 600;
      color: #94A3B8;
      letter-spacing: 0.1em;
      margin-bottom: 0.5rem;
      text-transform: uppercase;
    }
     
    /* Problem Title */
    .problem-title {
      font-family: 'Lora', Georgia, serif;
      font-size: 1.85rem;
      font-weight: 500;
      color: #0F172A;
      margin-bottom: 1.2rem;
    }
     
    /* Problem Description */
    .problem-desc {
      font-family: 'Lora', Georgia, serif;
      font-size: 1.1rem;
      line-height: 1.7;
      color: #334155;
      margin-bottom: 2rem;
    }
     
    /* Active Concept Box */
    .active-concept-box {
      border-left: 3px solid #0F172A;
      padding-left: 1.25rem;
      margin-top: 1.5rem;
      margin-bottom: 2.5rem;
    }
    .active-concept-label {
      font-family: 'Inter', sans-serif;
      font-size: 0.7rem;
      font-weight: 700;
      color: #64748B;
      letter-spacing: 0.08em;
      margin-bottom: 0.4rem;
      text-transform: uppercase;
    }
    .active-concept-text {
      font-family: 'Lora', Georgia, serif;
      font-size: 1.05rem;
      color: #1E293B;
      line-height: 1.5;
    }
     
    /* Study Notebook */
    .notebook-label-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.75rem;
    }
    .notebook-title {
      font-family: 'Inter', sans-serif;
      font-size: 0.75rem;
      font-weight: 700;
      color: #475569;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .notebook-counter {
      font-family: 'Inter', sans-serif;
      font-size: 0.7rem;
      color: #94A3B8;
    }
    .notebook-container {
      border: 1px solid #E2E8F0;
      background-color: #FAFAFA;
      border-radius: 6px;
      min-height: 250px;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 1.5rem;
    }
    .notebook-placeholder {
      font-family: 'Lora', Georgia, serif;
      font-style: italic;
      font-size: 0.95rem;
      color: #64748B;
      text-align: center;
    }
     
    /* Sidebar layout and headers */
    .sidebar-header {
      font-family: 'Inter', sans-serif;
      font-size: 0.75rem;
      font-weight: 700;
      color: #94A3B8;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      text-align: right;
      margin-bottom: 2rem;
      border-bottom: 1px solid #F1F5F9;
      padding-bottom: 0.5rem;
    }
     
    /* Chat bubble styles */
    .chat-role-label {
      font-family: 'Inter', sans-serif;
      font-size: 0.75rem;
      font-weight: 700;
      color: #0F172A;
      margin-top: 1.25rem;
      margin-bottom: 0.25rem;
    }
    .chat-text {
      font-family: 'Inter', sans-serif;
      font-size: 0.9rem;
      line-height: 1.5;
      color: #334155;
      margin-bottom: 1.25rem;
    }
    .status-indicator {
      font-family: 'Inter', sans-serif;
      font-size: 0.85rem;
      font-style: italic;
      color: #94A3B8;
      margin-top: 1rem;
    }
  </style>
""", unsafe_allow_html=True)

# CRITICAL CLOUD FIX: Use Docker-safe loopback address
BACKEND_URL = "http://127.0.0.1:8000"

# --- State Management Initialization ---
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "Socrates", "content": "Welcome to the workspace. Let's step through this physics problem together. How can I help you resolve the active step?"}
    ]
if "insights" not in st.session_state:
    st.session_state.insights = []
if "status_text" not in st.session_state:
    st.session_state.status_text = ""

# Automatically trigger session start on application launch
if st.session_state.get("session_id") is None:
    try:
        # Requesting mock session creation matching Problem 00899
        res = requests.post(f"{BACKEND_URL}/session/start/00899", timeout=3)
        if res.status_code == 200:
            st.session_state.session_id = res.json().get("session_id")
    except Exception:
        # Safe fallback for standalone UI development
        st.session_state.session_id = "sess_local_fallback"

# --- Top Navigation/Header Layer ---
now = dt.now()
date_string = now.strftime("%b %d · %I:%M %p").upper()

st.markdown(f"""
  <div class="header-container">
    <div class="header-title">PHYSICS TUTOR</div>
    <div class="header-date">{date_string}</div>
  </div>
""", unsafe_allow_html=True)

# --- Layout Grid: Main Workspace (col1) vs Socratic Companion Panel (col2) ---
col1, col2 = st.columns([13, 7])

with col1:
    # 1. Breadcrumbs
    st.markdown('<div class="breadcrumb">Class 12 · Electromagnetic Induction</div>', unsafe_allow_html=True)
     
    # 2. Problem Title
    st.markdown('<div class="problem-title">Problem 00899</div>', unsafe_allow_html=True)
     
    # 3. Problem Description with proper LaTeX parsing
    st.markdown("""
      <div class="problem-desc">
        A rectangular coil has $N = 100$ turns, with side lengths $ab = 30cm$ and $ad = 20cm$. 
        It is placed in a uniform magnetic field with a magnetic induction strength of $B = 0.8T$. 
        The coil rotates uniformly about the axis O' starting from the position shown in the diagram, 
        with an angular velocity of $\\omega = 100\\pi$ rad/s.
      </div>
    """, unsafe_allow_html=True)
     
    # 4. Active Concept blockquote
    st.markdown("""
      <div class="active-concept-box">
        <div class="active-concept-label">Active Concept</div>
        <div class="active-concept-text">
          Apply Faraday's law of electromagnetic induction to find the maximum induced electromotive force in a rotating coil.
        </div>
      </div>
    """, unsafe_allow_html=True)
     
    # 5. Study Notebook Component
    st.markdown(f"""
      <div class="notebook-label-row">
        <div class="notebook-title">Study Notebook</div>
        <div class="notebook-counter">{len(st.session_state.insights)} Insights Recorded</div>
      </div>
    """, unsafe_allow_html=True)
     
    if not st.session_state.insights:
        st.markdown("""
          <div class="notebook-container">
            <div class="notebook-placeholder">Awaiting formulas and insights from chat...</div>
          </div>
        """, unsafe_allow_html=True)
    else:
        # Dynamic rendering container for verified logic steps
        insight_box_html = '<div class="notebook-container" style="display: block; align-items: flex-start;">'
        for insight in st.session_state.insights:
            insight_box_html += f"""
              <div style="border-bottom: 1px solid #F1F5F9; padding-bottom: 0.75rem; margin-bottom: 0.75rem;">
                <span style="font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #475569;">
                  {insight.get('theorem')}
                </span><br/>
                <code style="font-family: monospace; font-size: 1rem; color: #0F172A;">{insight.get('formula')}</code>
                <span style="float: right; font-size: 0.85rem; color: #64748B;">Val: {insight.get('result')}</span>
              </div>
            """
        insight_box_html += "</div>"
        st.markdown(insight_box_html, unsafe_allow_html=True)

with col2:
    # Right Column - Socratic companion interface panel
    st.markdown('<div class="sidebar-header">Socratic Mode</div>', unsafe_allow_html=True)
     
    # Scrollable space layout
    chat_container = st.container()
     
    with chat_container:
        for chat_node in st.session_state.chat_history:
            st.markdown(f'<div class="chat-role-label">{chat_node["role"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-text">{chat_node["content"]}</div>', unsafe_allow_html=True)
         
        if st.session_state.status_text:
            st.markdown(f'<div class="status-indicator">{st.session_state.status_text}</div>', unsafe_allow_html=True)

    # Input controller bar
    with st.form("chat_form", clear_on_submit=True):
        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
        user_input = st.text_input(
            label="Hidden Form Label",
            placeholder="Type logic or formula...",
            label_visibility="collapsed"
        )
        submit_button = st.form_submit_button("SEND")
       
    if submit_button and user_input.strip() != "":
        # Append User input and trigger status loading state
        st.session_state.chat_history.append({"role": "You", "content": user_input})
        st.session_state.status_text = "Analyzing physics principles..."
        st.rerun()

# Processing step for active AI tutor callbacks
if st.session_state.status_text == "Analyzing physics principles...":
    last_user_message = st.session_state.chat_history[-1]["content"]
     
    # Send values over to Engine endpoint
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat/{st.session_state.session_id}",
            json={"user_text": last_user_message},
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.chat_history.append({
                "role": "Socrates",
                "content": data.get("ai_response")
            })
            # Save math concepts inside user's dynamic workspace
            nb_updates = data.get("notebook_updates", {})
            if nb_updates and nb_updates.get("official_solution"):
                st.session_state.insights.append(nb_updates["official_solution"])
        else:
            st.session_state.chat_history.append({
                "role": "Socrates",
                "content": "I apologize, but I've encountered an issue evaluating the equations. Let's try to look at this step again."
            })
    except Exception:
        # Failsafe if the API takes too long to wake up
        st.session_state.chat_history.append({
            "role": "Socrates",
            "content": "The logic engine is starting up. Please give me a second and try again!"
        })
       
    # Clear loading indicator status
    st.session_state.status_text = ""
    st.rerun()
