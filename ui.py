import streamlit as st
import requests
from datetime import datetime as dt
import textwrap

# --- GLOBAL LAYOUT CONFIGURATION ---
st.set_page_config(
    layout="wide", 
    initial_sidebar_state="collapsed", 
    page_title="AI Tutor Workspace"
)

BACKEND_URL = "http://127.0.0.1:8000"

# --- STATE MANAGEMENT ---
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
if "status_text" not in st.session_state:
    st.session_state.status_text = ""

# Auto-start or switch session if needed
def init_session(q_id):
    try:
        res = requests.post(f"{BACKEND_URL}/session/start/{q_id}", timeout=3)
        if res.status_code == 200:
            st.session_state.session_id = res.json().get("session_id")
            st.session_state.chat_history = [{"role": "assistant", "content": "Welcome. I'm ready to help you work through this physics problem. Where would you like to start?"}]
            st.session_state.insights = []
    except Exception:
        st.session_state.session_id = "sess_local_fallback"

if st.session_state.get("session_id") is None:
    init_session(st.session_state.current_question_id)

# --- NAVIGATION CALLBACKS ---
def nav_prev():
    # In a fully connected app, this would call the /questions/navigate endpoint
    # For now, it resets the current session for demonstration
    init_session(st.session_state.current_question_id)

def nav_next():
    init_session(st.session_state.current_question_id)

# --- I. APPLE-ESQUE MINIMALIST CSS ---
css_framework = textwrap.dedent("""
<style>
    /* Apple-System Typography & Clean Workspace */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #FFFFFF;
        color: #1D1D1F;
    }
    
    /* Hide Streamlit Cruft */
    header, footer, #MainMenu { display: none !important; }
    .block-container { padding: 2rem 4rem !important; max-width: 100% !important; }

    /* Header Utilities */
    .sys-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #E5E5EA; padding-bottom: 1rem; margin-bottom: 2rem; }
    .sys-time { font-size: 0.85rem; font-weight: 500; color: #86868B; letter-spacing: 0.02em; }
    
    /* Left Panel: Chat Interface */
    .chat-container { display: flex; flex-direction: column; gap: 16px; margin-bottom: 20px; }
    .chat-bubble { padding: 12px 16px; border-radius: 18px; max-width: 85%; font-size: 0.95rem; line-height: 1.5; }
    .chat-user { background-color: #F5F5F7; color: #1D1D1F; align-self: flex-end; border-bottom-right-radius: 4px; }
    .chat-ai { background-color: #FFFFFF; border: 1px solid #E5E5EA; color: #1D1D1F; align-self: flex-start; border-bottom-left-radius: 4px; }
    .status-text { font-size: 0.85rem; color: #86868B; font-style: italic; align-self: flex-start; margin-left: 10px; }

    /* Right Panel: Typography */
    .tag { font-size: 0.75rem; font-weight: 600; color: #86868B; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 8px; }
    .title { font-size: 2rem; font-weight: 600; letter-spacing: -0.02em; color: #1D1D1F; margin-bottom: 16px; }
    
    /* Right Panel: Notebook */
    .notebook-section { margin-top: 3rem; border-top: 1px solid #E5E5EA; padding-top: 2rem; }
    .notebook-header { font-size: 0.85rem; font-weight: 600; color: #1D1D1F; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 1rem; }
    .notebook-card { background-color: #F5F5F7; border-radius: 12px; padding: 16px; margin-bottom: 12px; border: 1px solid transparent; transition: border 0.2s ease;}
    .notebook-card:hover { border: 1px solid #D2D2D7; }
    .card-label { font-size: 0.75rem; font-weight: 600; color: #86868B; text-transform: uppercase; margin-bottom: 6px; }
    .card-value { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 1.1rem; color: #1D1D1F; }

    /* Streamlit Overrides for Buttons and Inputs */
    [data-testid="stButton"] button { border-radius: 20px; border: 1px solid #E5E5EA; background: #FFFFFF; color: #1D1D1F; font-weight: 500; transition: all 0.2s ease; }
    [data-testid="stButton"] button:hover { background: #F5F5F7; border-color: #D2D2D7; color: #1D1D1F;}
    [data-testid="stChatInput"] { border: 1px solid #E5E5EA !important; border-radius: 24px !important; background: #F5F5F7 !important; }
    [data-testid="stChatInput"]:focus-within { background: #FFFFFF !important; border-color: #0071E3 !important; box-shadow: 0 0 0 3px rgba(0,113,227,0.1) !important; }
</style>
""")
st.markdown(css_framework, unsafe_allow_html=True)

# --- II. HEADER & CONTROLS ---
now = dt.now()
time_str = now.strftime("%A, %B %d | %I:%M %p").upper()

st.markdown(f'<div class="sys-time">{time_str}</div>', unsafe_allow_html=True)
st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)

h_col1, h_col2, h_col3 = st.columns([1, 8, 1])
with h_col1:
    st.button("← Prev", on_click=nav_prev, use_container_width=True)
with h_col3:
    st.button("Next →", on_click=nav_next, use_container_width=True)

st.markdown('<div style="border-bottom: 1px solid #E5E5EA; margin-bottom: 2rem;"></div>', unsafe_allow_html=True)


# --- III. MAIN WORKSPACE SPLIT ---
# Left: Chat (40%), Right: Question & Notebook (60%)
left_col, right_col = st.columns([4, 6], gap="large")

# ==========================================
# LEFT PANEL: AI TUTOR CHAT
# ==========================================
with left_col:
    # We construct the chat feed using Apple-style bubbles
    chat_html = '<div class="chat-container">'
    
    for msg in st.session_state.chat_history:
        if msg["role"] == "You":
            chat_html += f'<div class="chat-bubble chat-user">{msg["content"]}</div>'
        else:
            chat_html += f'<div class="chat-bubble chat-ai">{msg["content"]}</div>'
            
    if st.session_state.status_text:
        chat_html += f'<div class="status-text">{st.session_state.status_text}</div>'
        
    chat_html += '</div>'
    
    # Render Chat
    st.markdown(chat_html, unsafe_allow_html=True)
    
    # Render Input 
    user_input = st.chat_input("Message Tutor...")
    
    if user_input:
        st.session_state.chat_history.append({"role": "You", "content": user_input})
        st.session_state.status_text = "Thinking..."
        st.rerun()

# ==========================================
# RIGHT PANEL: QUESTION & NOTEBOOK
# ==========================================
with right_col:
    # Tags & Title
    st.markdown('<div class="tag">Physics · Electromagnetic Induction</div>', unsafe_allow_html=True)
    st.markdown('<div class="title">Problem 00899</div>', unsafe_allow_html=True)
    
    # Problem Description (Native Markdown ensures LaTeX works perfectly)
    st.markdown("""
    A rectangular coil has $N = 100$ turns, with side lengths $ab = 30cm$ and $ad = 20cm$. 
    It is placed in a uniform magnetic field with a magnetic induction strength of $B = 0.8T$. 
    The coil rotates uniformly about the axis O' starting from the position shown in the diagram, 
    with an angular velocity of $\\omega = 100\\pi$ rad/s.
    
    **Active Task:** Apply Faraday's law of electromagnetic induction to find the maximum induced electromotive force in a rotating coil.
    """)
    
    # Study Notebook Section
    st.markdown('<div class="notebook-section"><div class="notebook-header">Study Notebook</div>', unsafe_allow_html=True)
    
    if not st.session_state.insights:
        st.markdown('<div style="color: #86868B; font-style: italic; font-size: 0.9rem;">No insights recorded yet. Talk to the tutor to begin unlocking steps.</div></div>', unsafe_allow_html=True)
    else:
        for insight in st.session_state.insights:
            st.markdown(f"""
            <div class="notebook-card">
                <div class="card-label">{insight.get('theorem', 'Physics Principle')}</div>
                <div class="card-value">{insight.get('formula', '')}</div>
                <div style="font-size: 0.85rem; color: #86868B; margin-top: 8px;">Final Value: {insight.get('result', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# BACKEND PROCESSOR
# ==========================================
if st.session_state.status_text == "Thinking...":
    last_user_message = st.session_state.chat_history[-1]["content"]
     
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat/{st.session_state.session_id}",
            json={"user_text": last_user_message},
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": data.get("ai_response")
            })
            nb_updates = data.get("notebook_updates", {})
            if nb_updates and nb_updates.get("official_solution"):
                st.session_state.insights.append(nb_updates["official_solution"])
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "System error: Feedback loop disrupted."
            })
    except Exception:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "API synchronization in progress. Please hold."
        })
       
    st.session_state.status_text = ""
    st.rerun()
