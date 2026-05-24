import streamlit as st
import requests
import datetime
import textwrap

# --- GLOBAL LAYOUT CONFIGURATION ---
st.set_page_config(layout="wide", initial_sidebar_state="collapsed", page_title="Learning Platform")

BACKEND_URL = "http://127.0.0.1:8000"

if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "System initialized. Asynchronous learning session active."}
    ]
if "insights" not in st.session_state:
    st.session_state.insights = []
if "status_text" not in st.session_state:
    st.session_state.status_text = ""

# Auto-start session silently
if st.session_state.get("session_id") is None:
    try:
        res = requests.post(f"{BACKEND_URL}/session/start/00899", timeout=3)
        if res.status_code == 200:
            st.session_state.session_id = res.json().get("session_id")
    except Exception:
        st.session_state.session_id = "sess_local_fallback"

# --- I. GLOBAL LAYOUT FRAMEWORK (CSS) ---
# textwrap.dedent removes indentation so Streamlit doesn't create gray code blocks
css_framework = textwrap.dedent("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Georgia&display=swap');

    /* Viewport Config */
    html, body, [data-testid="stAppViewContainer"] {
        height: 100vh;
        width: 100vw;
        overflow: hidden;
        margin: 0;
        padding: 0;
        background-color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit Cruft */
    header, footer, #MainMenu { display: none !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    /* Header Section */
    .global-header {
        height: 60px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 6%;
        border-bottom: 1px solid #e9ecef;
        background-color: #ffffff;
    }
    .header-brand { font-size: 0.9rem; font-weight: 700; letter-spacing: 0.05em; color: #212529; }
    .header-utility { font-size: 0.85rem; color: #6c757d; }

    /* Main Workspace Split - Target Streamlit Columns */
    [data-testid="column"]:nth-of-type(1) {
        height: calc(100vh - 60px);
        padding: 2% 5% 5% 10% !important;
        overflow-y: auto;
    }
    [data-testid="column"]:nth-of-type(2) {
        height: calc(100vh - 60px);
        padding: 30px !important;
        background-color: #f8f9fa;
        border-left: 1px solid #e9ecef;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
    }

    /* Primary Left Panel Typography */
    .breadcrumb { font-size: 0.7rem; color: #6c757d; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 20px; font-weight: 600; }
    .main-id-header { font-family: 'Georgia', serif; font-size: 1.8rem; font-weight: bold; color: #212529; margin-bottom: 25px; }
    .body-desc { font-family: 'Georgia', serif; font-size: 1.05rem; line-height: 1.6; color: #333333; margin-bottom: 35px; }
    
    /* Active Context Container */
    .context-container { border-left: 3px solid #212529; padding-left: 20px; margin-bottom: 60px; }
    .context-label { font-size: 0.7rem; color: #6c757d; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; margin-bottom: 8px; }
    .context-desc { font-family: 'Georgia', serif; font-size: 0.95rem; color: #212529; line-height: 1.5; }

    /* Study Notebook */
    .notebook-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 10px; }
    .notebook-label { font-size: 0.75rem; font-weight: 700; color: #212529; text-transform: uppercase; letter-spacing: 0.05em; }
    .notebook-counter { font-size: 0.7rem; color: #adb5bd; }
    .notebook-workspace { background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; min-height: 30vh; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 20px;}
    .notebook-placeholder { font-family: 'Georgia', serif; font-style: italic; color: #adb5bd; font-size: 0.95rem; }
    .notebook-item { width: 100%; border-bottom: 1px solid #e9ecef; padding-bottom: 15px; margin-bottom: 15px; }

    /* Secondary Right Panel Typography */
    .chat-header { border-bottom: 1px solid #e9ecef; padding-bottom: 10px; margin-bottom: 20px; }
    .chat-header-main { font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: #212529; letter-spacing: 0.05em; }
    .chat-header-sub { font-size: 0.75rem; color: #6c757d; margin-top: 4px; }
    
    .chat-stream { flex-grow: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; margin-bottom: 20px; }
    
    .msg-block { display: flex; flex-direction: column; width: 100%; }
    .msg-block.assistant { align-items: flex-start; }
    .msg-block.user { align-items: flex-end; }
    
    .msg-sender { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; color: #6c757d; margin-bottom: 6px; }
    .msg-content { font-size: 0.9rem; line-height: 1.5; color: #212529; padding: 12px 16px; border-radius: 6px; }
    .msg-block.assistant .msg-content { background-color: #ffffff; border: 1px solid #e9ecef; width: 100%; }
    .msg-block.user .msg-content { background-color: #e9ecef; max-width: 85%; }
    
    .status-feedback { font-family: 'Georgia', serif; font-style: italic; font-size: 0.85rem; color: #adb5bd; }

    /* Streamlit Input Wrapper Override */
    [data-testid="stChatInput"] { border: 1px solid #e9ecef !important; border-radius: 45px !important; background: #ffffff !important; padding-right: 5px !important;}
</style>
""")

st.markdown(css_framework, unsafe_allow_html=True)

# --- GLOBAL HEADER ---
current_time = datetime.datetime.now().strftime("%Y-%m-%d | %H:%M UTC")
header_html = f"""
<div class="global-header">
    <div class="header-brand">PLATFORM INTERFACE</div>
    <div class="header-utility">{current_time}</div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# --- WORKSPACE SPLIT ---
col1, col2 = st.columns([6, 4], gap="small")

# --- II. PRIMARY LEFT PANEL ---
with col1:
    
    if not st.session_state.insights:
        notebook_content = '<span class="notebook-placeholder">Workspace empty. Awaiting asynchronous input...</span>'
    else:
        notebook_content = ""
        for insight in st.session_state.insights:
            notebook_content += f"""
            <div class="notebook-item">
                <div style="font-size: 0.7rem; font-weight: 600; color: #6c757d; margin-bottom: 5px;">{insight.get('theorem')}</div>
                <div style="font-family: monospace; font-size: 1rem; color: #212529;">{insight.get('formula')}</div>
            </div>
            """

    left_panel_html = f"""
<div class="breadcrumb">CATEGORY / SUB-MODULE AREA</div>

<div class="main-id-header">Main Content ID Header</div>

<div class="body-desc">
    This is the body description block. It hosts the multi-line structural content zone, styled entirely in a highly legible serif typography system. The text here spans multiple lines to establish visual weight and reading rhythm before handing off to the interactive elements below.
</div>

<div class="context-container">
    <div class="context-label">Active Context Container</div>
    <div class="context-desc">Inner description field formatting. Anchored by the structural left-border indicator.</div>
</div>

<div class="notebook-header">
    <span class="notebook-label">Study Notebook Element</span>
    <span class="notebook-counter">{len(st.session_state.insights)} ENTRIES LOGGED</span>
</div>

<div class="notebook-workspace">
    {notebook_content}
</div>
"""
    st.markdown(left_panel_html, unsafe_allow_html=True)


# --- III. SECONDARY RIGHT PANEL ---
with col2:
    
    # Right panel structure
    chat_html = """
<div class="chat-header">
    <div class="chat-header-main">Interactive Chat Interface</div>
    <div class="chat-header-sub">System Status: Awaiting User Input</div>
</div>

<div class="chat-stream">
"""
    for msg in st.session_state.chat_history:
        role_class = "user" if msg["role"] == "You" else "assistant"
        sender_name = "User Profile" if msg["role"] == "You" else "Assistant Profile"
        
        chat_html += f"""
    <div class="msg-block {role_class}">
        <div class="msg-sender">{sender_name}</div>
        <div class="msg-content">{msg["content"]}</div>
    </div>
"""
        
    if st.session_state.status_text:
        chat_html += f"""
    <div class="msg-block assistant">
        <div class="status-feedback">{st.session_state.status_text}</div>
    </div>
"""
        
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)

    # Input Box Tool
    user_input = st.chat_input("Type your response here...")
    
    if user_input:
        st.session_state.chat_history.append({"role": "You", "content": user_input})
        st.session_state.status_text = "Processing asynchronous request..."
        st.rerun()

# --- BACKEND LOGIC ROUTER ---
if st.session_state.status_text == "Processing asynchronous request...":
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
