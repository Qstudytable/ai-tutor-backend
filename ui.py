import streamlit as st
import requests
from datetime import datetime as dt

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Physics Tutor Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CRITICAL CLOUD FIX: Use Docker-safe loopback address
BACKEND_URL = "http://127.0.0.1:8000"

# --- STATE MANAGEMENT ---
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

# Auto-start session
if st.session_state.get("session_id") is None:
    try:
        res = requests.post(f"{BACKEND_URL}/session/start/00899", timeout=3)
        if res.status_code == 200:
            st.session_state.session_id = res.json().get("session_id")
    except Exception:
        st.session_state.session_id = "sess_local_fallback"

# --- INJECT EXACT HTML/CSS TEMPLATE ---
st.markdown("""
    <style>
        /* Import Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Georgia&display=swap');

        /* Hide Default Streamlit Elements */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Master Reset for Streamlit Container */
        .stApp, [data-testid="stAppViewContainer"] {
            background-color: #FFFFFF !important;
        }
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
            overflow-x: hidden;
        }

        /* --- VARIABLES --- */
        :root {
            --bg-main: #FFFFFF;
            --bg-subtle: #F8FAFC;
            --slate-900: #0F172A;
            --slate-600: #475569;
            --slate-400: #94A3B8;
            --border-light: #E2E8F0;
            --font-ui: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-academic: 'Georgia', ui-serif, serif;
        }

        /* --- HEADER --- */
        .top-header {
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            padding: 0 40px; 
            height: 56px;
            border-bottom: 1px solid var(--border-light);
            background-color: var(--bg-main);
            font-family: var(--font-ui);
        }
        .top-header .logo { font-weight: 600; font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase; color: var(--slate-900); }
        .top-header .session-clock { font-weight: 500; font-size: 11px; color: var(--slate-600); letter-spacing: 1px; text-transform: uppercase; }

        /* --- HACKING STREAMLIT COLUMNS TO MATCH 80/20 LAYOUT --- */
        [data-testid="column"]:nth-of-type(1) {
            padding: 48px 40px 0 40px !important;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        [data-testid="column"]:nth-of-type(2) {
            border-left: 1px solid var(--border-light);
            padding: 32px 24px !important;
            background: var(--bg-main);
            height: 100vh;
        }

        /* --- LEFT COLUMN DOM --- */
        .content-column { width: 100%; max-width: 760px; font-family: var(--font-ui); }
        .breadcrumbs { font-size: 11px; font-weight: 600; color: var(--slate-400); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 24px; }
        .problem-heading { font-size: 22px; font-weight: 500; letter-spacing: -0.5px; margin-bottom: 24px; color: var(--slate-900); }
        .problem-text { font-family: var(--font-academic); font-size: 18px; line-height: 1.7; color: var(--slate-900); margin-bottom: 48px; }
        
        .concept-block { border-left: 2px solid var(--slate-900); padding-left: 24px; margin-bottom: 48px; }
        .concept-block strong { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--slate-600); display: block; margin-bottom: 8px;}
        .concept-block p { font-family: var(--font-academic); font-size: 16px; line-height: 1.6; color: var(--slate-900); margin: 0;}

        /* Notebook */
        .notebook-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 12px; }
        .notebook-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--slate-900); }
        .notebook-meta { font-size: 11px; color: var(--slate-400); }
        .notebook-area { border: 1px solid var(--border-light); background-color: var(--bg-subtle); border-radius: 4px; display: flex; align-items: center; justify-content: center; min-height: 160px; margin-bottom: 48px; padding: 24px;}
        .notebook-empty { font-family: var(--font-academic); font-style: italic; color: var(--slate-600); font-size: 15px; }

        /* --- RIGHT COLUMN DOM --- */
        .chat-feed { display: flex; flex-direction: column; gap: 32px; font-family: var(--font-ui); margin-bottom: 24px; }
        .chat-mode-label { align-self: center; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: var(--slate-400); margin-bottom: 8px; text-align: center;}
        .msg-row { display: flex; flex-direction: column; }
        .msg-label { font-size: 11px; font-weight: 600; color: var(--slate-900); margin-bottom: 6px; }
        .msg-label.user { color: var(--slate-600); }
        .msg-content { font-size: 14px; line-height: 1.6; color: var(--slate-900); }
        .thinking { font-size: 13px; color: var(--slate-400); font-style: italic; }

        /* Streamlit Input Override to match custom box */
        [data-testid="stChatInput"] {
            border: 1px solid var(--border-light) !important;
            border-radius: 8px !important;
            background: var(--bg-subtle) !important;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: var(--slate-400) !important;
            background: var(--bg-main) !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- TOP HEADER BAR ---
now = dt.now()
date_string = now.strftime("%b %d ‧ %I:%M %p").upper()
st.markdown(f"""
    <div class="top-header">
        <div class="logo">Physics Tutor</div>
        <div class="session-clock">{date_string}</div>
    </div>
""", unsafe_allow_html=True)

# --- 80/20 WORKSPACE LAYOUT ---
col1, col2 = st.columns([4, 1.5], gap="small")

# --- LEFT PANE (DEEP WORK) ---
with col1:
    
    # Render Notebook Contents
    if not st.session_state.insights:
        notebook_html = '<div class="notebook-area"><span class="notebook-empty">Awaiting formulas and insights from chat...</span></div>'
    else:
        notebook_html = '<div class="notebook-area" style="flex-direction: column; align-items: stretch; justify-content: flex-start; gap: 16px;">'
        for insight in st.session_state.insights:
            notebook_html += f"""
            <div style="border-bottom: 1px solid var(--border-light); padding-bottom: 12px;">
                <strong style="font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--slate-600); display: block; margin-bottom: 4px;">{insight.get('theorem')}</strong>
                <div style="font-family: monospace; font-size: 16px; color: var(--slate-900); margin-bottom: 4px;">{insight.get('formula')}</div>
                <div style="font-size: 12px; color: var(--slate-400);">Value: {insight.get('result', 'N/A')}</div>
            </div>
            """
        notebook_html += '</div>'

    # Inject Entire Left DOM
    st.markdown(f"""
        <div class="content-column">
            <div class="breadcrumbs">Class 12 ‧ Electromagnetic Induction</div>
            <div class="problem-heading">Problem 00899</div>
            
            <div class="problem-text">
                A rectangular coil has <i>N = 100</i> turns, with side lengths <i>ab = 30cm</i> and <i>ad = 20cm</i>. 
                It is placed in a uniform magnetic field with a magnetic induction strength of <i>B = 0.8T</i>. 
                The coil rotates uniformly about the axis O' starting from the position shown in the diagram, 
                with an angular velocity of <i>&omega; = 100&pi;</i> rad/s.
            </div>
            
            <div class="concept-block">
                <strong>Active Concept</strong>
                <p>Apply Faraday's law of electromagnetic induction to find the maximum induced electromotive force in a rotating coil.</p>
            </div>

            <div class="notebook-header">
                <span class="notebook-title">Study Notebook</span>
                <span class="notebook-meta">{len(st.session_state.insights)} Insights Recorded</span>
            </div>
            
            {notebook_html}
        </div>
    """, unsafe_allow_html=True)

# --- RIGHT PANE (CHAT UTILITY) ---
with col2:
    
    # Generate Chat Feed DOM
    chat_html = '<div class="chat-feed"><div class="chat-mode-label">Socratic Mode</div>'
    
    for msg in st.session_state.chat_history:
        role = msg["role"]
        is_user = role == "You"
        label_class = "msg-label user" if is_user else "msg-label"
        display_name = "You" if is_user else "Socrates"
        content = msg["content"]
        
        chat_html += f"""
        <div class="msg-row">
            <div class="{label_class}">{display_name}</div>
            <div class="msg-content">{content}</div>
        </div>
        """
        
    if st.session_state.status_text:
        chat_html += f"""
        <div class="msg-row">
            <div class="thinking">{st.session_state.status_text}</div>
        </div>
        """
        
    chat_html += '</div>'
    
    # Inject Chat DOM
    st.markdown(chat_html, unsafe_allow_html=True)

    # Input Box at bottom of column
    user_input = st.chat_input("Type logic or formula...")
    
    if user_input:
        st.session_state.chat_history.append({"role": "You", "content": user_input})
        st.session_state.status_text = "Analyzing physics principles..."
        st.rerun()

# --- BACKEND PROCESSOR (Runs if status indicates loading) ---
if st.session_state.status_text == "Analyzing physics principles...":
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
                "role": "Socrates",
                "content": data.get("ai_response")
            })
            nb_updates = data.get("notebook_updates", {})
            if nb_updates and nb_updates.get("official_solution"):
                st.session_state.insights.append(nb_updates["official_solution"])
        else:
            st.session_state.chat_history.append({
                "role": "Socrates",
                "content": "I apologize, but I've encountered an issue evaluating the equations. Let's try to look at this step again."
            })
    except Exception:
        st.session_state.chat_history.append({
            "role": "Socrates",
            "content": "The logic engine is starting up. Please give me a second and try again!"
        })
       
    st.session_state.status_text = ""
    st.rerun()
