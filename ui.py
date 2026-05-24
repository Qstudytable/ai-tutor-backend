import streamlit as st
import requests
from datetime import datetime as dt
import textwrap

# --- GLOBAL LAYOUT CONFIGURATION ---
st.set_page_config(
    layout="wide", 
    initial_sidebar_state="collapsed", 
    page_title="AI Tutor"
)

BACKEND_URL = "http://127.0.0.1:8000"

# --- STATE MANAGEMENT ---
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "current_question_id" not in st.session_state:
    st.session_state.current_question_id = "00899"
if "problem_context" not in st.session_state:
    st.session_state.problem_context = "A rectangular coil has $N = 100$ turns..."
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "insights" not in st.session_state:
    st.session_state.insights = []
if "status_text" not in st.session_state:
    st.session_state.status_text = ""

def init_session(q_id):
    try:
        res = requests.post(f"{BACKEND_URL}/session/start/{q_id}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.session_state.session_id = data.get("session_id")
            st.session_state.current_question_id = data.get("question_id")
            if data.get("context"):
                st.session_state.problem_context = data.get("context")
            st.session_state.chat_history = [{"role": "assistant", "content": "Welcome. I'm ready to help you work through this physics problem. Where would you like to start?"}]
            st.session_state.insights = []
    except Exception:
        st.session_state.session_id = "sess_local_fallback"

if st.session_state.get("session_id") is None:
    init_session(st.session_state.current_question_id)

def nav_prev():
    try:
        res = requests.get(f"{BACKEND_URL}/questions/navigate/{st.session_state.current_question_id}/prev", timeout=3)
        if res.status_code == 200:
            init_session(res.json().get("question_id"))
    except Exception:
        pass

def nav_next():
    try:
        res = requests.get(f"{BACKEND_URL}/questions/navigate/{st.session_state.current_question_id}/next", timeout=3)
        if res.status_code == 200:
            init_session(res.json().get("question_id"))
    except Exception:
        pass

# --- I. APPLE-ESQUE MINIMALIST CSS ---
css_framework = textwrap.dedent("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #FFFFFF;
        color: #1D1D1F;
    }
    header, footer, #MainMenu { display: none !important; }
    .block-container { padding: 3rem 5rem !important; max-width: 100% !important; }

    .sys-time { font-size: 0.85rem; font-weight: 500; color: #86868B; letter-spacing: 0.04em; }
    
    .chat-wrapper { height: 60vh; overflow-y: auto; padding-right: 1.5rem; display: flex; flex-direction: column; gap: 1.5rem; margin-bottom: 1.5rem; scroll-behavior: smooth; }
    .chat-wrapper::-webkit-scrollbar { width: 6px; }
    .chat-wrapper::-webkit-scrollbar-track { background: transparent; }
    .chat-wrapper::-webkit-scrollbar-thumb { background: #E5E5EA; border-radius: 10px; }
    .chat-wrapper::-webkit-scrollbar-thumb:hover { background: #D2D2D7; }

    .chat-bubble { padding: 14px 20px; border-radius: 20px; max-width: 85%; font-size: 1rem; line-height: 1.6; }
    .chat-user { background-color: #F5F5F7; color: #1D1D1F; align-self: flex-end; border-bottom-right-radius: 4px; }
    .chat-ai { background-color: #FFFFFF; border: 1px solid #E5E5EA; color: #1D1D1F; align-self: flex-start; border-bottom-left-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }
    
    .typing-indicator { display: flex; align-items: center; gap: 5px; padding: 4px 6px; }
    .typing-indicator span { width: 8px; height: 8px; background-color: #86868B; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
    .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
    .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
    @keyframes bounce { 0%, 80%, 100% { transform: scale(0); opacity: 0.4; } 40% { transform: scale(1); opacity: 1; } }

    .tag { font-size: 0.75rem; font-weight: 600; color: #86868B; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 12px; }
    .title { font-size: 2.2rem; font-weight: 600; letter-spacing: -0.02em; color: #1D1D1F; margin-bottom: 24px; }
    
    /* Removed custom .problem-desc class mapping to allow native Streamlit Markdown to handle LaTeX properly */
    
    .notebook-section { margin-top: 4rem; border-top: 1px solid #E5E5EA; padding-top: 3rem; }
    .notebook-header { font-size: 0.85rem; font-weight: 600; color: #1D1D1F; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 1.5rem; }
    .notebook-card { background-color: #FFFFFF; border-radius: 12px; padding: 20px; margin-bottom: 16px; border: 1px solid #E5E5EA; transition: box-shadow 0.2s ease; animation: fade-in 0.4s ease-out;}
    .notebook-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.04); }
    .card-label { font-size: 0.75rem; font-weight: 600; color: #86868B; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.04em;}
    .card-value { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 1.2rem; color: #1D1D1F; }
    @keyframes fade-in { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

    [data-testid="stButton"] button { border-radius: 24px; border: 1px solid #E5E5EA; background: #FFFFFF; color: #1D1D1F; font-weight: 500; padding: 0.5rem 1.5rem; transition: all 0.2s ease; }
    [data-testid="stButton"] button:hover { background: #F5F5F7; border-color: #D2D2D7; color: #1D1D1F;}
    [data-testid="stChatInput"] { border: 1px solid #E5E5EA !important; border-radius: 24px !important; background: #F5F5F7 !important; padding: 0.5rem !important;}
    [data-testid="stChatInput"]:focus-within { background: #FFFFFF !important; border-color: #0071E3 !important; box-shadow: 0 0 0 3px rgba(0,113,227,0.1) !important; }
</style>
""")
st.markdown(css_framework, unsafe_allow_html=True)

# --- II. HEADER & CONTROLS ---
now = dt.now()
time_str = now.strftime("%A, %B %d | %I:%M %p").upper()

st.markdown(f'<div class="sys-time">{time_str}</div>', unsafe_allow_html=True)
st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)

h_col1, h_col2, h_col3 = st.columns([1, 10, 1])
with h_col1:
    st.button("← Prev", on_click=nav_prev, use_container_width=True)
with h_col3:
    st.button("Next →", on_click=nav_next, use_container_width=True)

st.markdown('<div style="border-bottom: 1px solid #E5E5EA; margin-bottom: 3rem;"></div>', unsafe_allow_html=True)


# --- III. MAIN WORKSPACE SPLIT ---
left_col, right_col = st.columns([5.5, 4.5], gap="large")

with left_col:
    st.markdown('<div class="tag">Physics · Practice Module</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="title">Problem {st.session_state.current_question_id}</div>', unsafe_allow_html=True)
    
    # Native Streamlit markdown correctly parses all LaTeX tags seamlessly
    st.markdown(f"<div style='font-size: 1.15rem; line-height: 1.8; color: #1D1D1F;'>{st.session_state.problem_context}</div>", unsafe_allow_html=True)
    
    st.markdown('<div class="notebook-section"><div class="notebook-header">Study Notebook</div>', unsafe_allow_html=True)
    
    if not st.session_state.insights:
        st.markdown('<div style="color: #86868B; font-style: italic; font-size: 0.95rem;">No insights recorded yet. Talk to the tutor to begin unlocking steps.</div></div>', unsafe_allow_html=True)
    else:
        for insight in st.session_state.insights:
            st.markdown(f"""
            <div class="notebook-card">
                <div class="card-label">{insight.get('theorem', 'Physics Principle')}</div>
                <div class="card-value">{insight.get('formula', '')}</div>
                <div style="font-size: 0.85rem; color: #86868B; margin-top: 10px;">Final Value: {insight.get('result', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    chat_html = '<div class="chat-wrapper" id="chat-stream">'
    
    for msg in st.session_state.chat_history:
        if msg["role"] == "You":
            chat_html += f'<div class="chat-bubble chat-user">{msg["content"]}</div>'
        else:
            chat_html += f'<div class="chat-bubble chat-ai">{msg["content"]}</div>'
            
    if st.session_state.status_text == "Thinking...":
        chat_html += """
        <div class="chat-bubble chat-ai" style="padding: 12px 18px; width: fit-content;">
            <div class="typing-indicator"><span></span><span></span><span></span></div>
        </div>
        """
        
    chat_html += '</div>'
    
    # THE FIX: Directly inject the styled HTML, NO TERNARY OPERATOR to trigger magic text output.
    st.markdown(chat_html, unsafe_allow_html=True)
    
    # THE FIX: Isolate the auto-scroll Javascript in a hidden, size-zero iframe to keep things clean.
    st.components.v1.html(
        "<script>const chat = window.parent.document.getElementById('chat-stream'); if (chat) chat.scrollTop = chat.scrollHeight;</script>", 
        height=0, width=0
    )
    
    user_input = st.chat_input("Message Tutor...")
    
    if user_input:
        st.session_state.chat_history.append({"role": "You", "content": user_input})
        st.session_state.status_text = "Thinking..."
        st.rerun()

# --- BACKEND PROCESSOR ---
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
            st.session_state.chat_history.append({"role": "assistant", "content": data.get("ai_response")})
            nb_updates = data.get("notebook_updates", {})
            if nb_updates and nb_updates.get("official_solution"):
                st.session_state.insights.append(nb_updates["official_solution"])
        else:
            st.session_state.chat_history.append({"role": "assistant", "content": "System error: Feedback loop disrupted."})
    except Exception:
        st.session_state.chat_history.append({"role": "assistant", "content": "API synchronization in progress. Please hold."})
       
    st.session_state.status_text = ""
    st.rerun()
