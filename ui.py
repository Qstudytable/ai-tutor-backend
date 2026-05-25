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

BACKEND_URL = "http://127.0.0.1:8000"

# --- STATE MANAGEMENT ---
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
if "question_title" not in st.session_state:
    st.session_state.question_title = "Physics Dynamics Problem"
if "question_topic" not in st.session_state:
    st.session_state.question_topic = "Classical Mechanics"
if "tutoring_mode" not in st.session_state:
    st.session_state.tutoring_mode = "Active — Socratic Mode"
if "active_concept" not in st.session_state:
    st.session_state.active_concept = ""


def extract_dynamic_metadata(data: dict):
    topic = data.get("topic") or data.get("subject") or data.get("category")
    title = data.get("title") or data.get("question_name")
    if not topic:
        context_lower = st.session_state.question_context.lower()
        if "collides" in context_lower or "velocity" in context_lower or "mass" in context_lower:
            topic = "Classical Mechanics"
        elif "magnetic" in context_lower or "electromotive" in context_lower or "induction" in context_lower:
            topic = "Electromagnetism"
        else:
            topic = "General Physics"
    if not title:
        title = f"Problem {st.session_state.current_question_id}"
    st.session_state.question_topic = topic
    st.session_state.question_title = title
    st.session_state.active_concept = data.get("active_concept") or data.get("concept") or ""


def sync_session_snapshot(session_id: str):
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
            st.error("Navigation failed.")
    except Exception as e:
        st.error(f"Internal navigation failed: {e}")


# --- INITIALIZATION RUNNER ---
if st.session_state.session_id is None:
    init_session(st.session_state.current_question_id)
else:
    sync_session_snapshot(st.session_state.session_id)


def clean_html(html_str: str) -> str:
    return "\n".join(line.strip() for line in html_str.strip().split("\n"))


# ============================================================
# GLOBAL CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
.main, .block-container,
[data-testid="stVerticalBlock"] {
    background-color: #FFFFFF !important;
    color: #121212 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

header[data-testid="stHeader"], footer, #MainMenu { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

.ws-header {
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
.ws-brand {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #121212;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.ws-timestamp {
    font-size: 11px;
    color: #5A5A57;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 500;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

[data-testid="column"]:nth-of-type(1) {
    border-right: 1px solid #EAE8E3;
    height: calc(100vh - 64px);
    padding: 2.5rem 0.5rem !important;
    display: flex;
    flex-direction: column;
    align-items: center;
    background-color: #FFFFFF;
    overflow: hidden;
}
[data-testid="column"]:nth-of-type(2) {
    padding: 3.5rem 5% !important;
    overflow-y: auto;
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
}

.sidebar-topic {
    font-size: 9px;
    color: #90908C;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    writing-mode: vertical-rl;
    transform: rotate(180deg);
    flex: 1;
    text-align: center;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.sidebar-id {
    font-size: 10px;
    color: #5A5A57;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    text-align: center;
    margin-top: 0.75rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

div.stButton > button {
    border: none !important;
    background-color: transparent !important;
    color: #5A5A57 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    padding: 0.25rem 0.1rem !important;
    line-height: 1 !important;
    height: auto !important;
    min-height: unset !important;
    white-space: nowrap !important;
    width: 100% !important;
    border-radius: 0 !important;
    box-shadow: none !important;
}
div.stButton > button:hover {
    color: #121212 !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
div.stButton > button:focus,
div.stButton > button:active {
    box-shadow: none !important;
    border: none !important;
    outline: none !important;
}

.problem-meta-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #90908C;
    margin-bottom: 1rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.problem-heading {
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 2.2rem !important;
    font-weight: 400 !important;
    line-height: 1.2 !important;
    color: #121212 !important;
    letter-spacing: -0.01em !important;
    margin: 0 0 1.75rem 0 !important;
}

[data-testid="column"]:nth-of-type(2) h1,
[data-testid="column"]:nth-of-type(2) h2 {
    font-family: 'EB Garamond', Georgia, serif !important;
    font-weight: 400 !important;
    color: #121212 !important;
}

.stMarkdown p {
    font-family: 'EB Garamond', serif !important;
    font-size: 16px !important;
    line-height: 1.85 !important;
    color: #121212 !important;
}
.stMarkdown p .katex,
.stMarkdown p .katex * {
    font-family: KaTeX_Main, 'Times New Roman', serif !important;
}

.active-concept-block {
    border-left: 2px solid #121212;
    padding: 0.85rem 1.25rem;
    margin: 2rem 0 2.5rem 0;
    background-color: #FAFAF9;
}
.active-concept-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #90908C;
    margin-bottom: 0.5rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.active-concept-text {
    font-family: 'EB Garamond', serif;
    font-size: 16px;
    line-height: 1.8;
    color: #121212;
    margin: 0;
}

.notebook-wrapper {
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid #EAE8E3;
}
.notebook-header-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 1.25rem;
}
.notebook-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #5A5A57;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.notebook-count {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #90908C;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.notebook-placeholder-box {
    border: 1px solid #DEDAD5;
    border-radius: 8px;
    padding: 3rem 1.5rem;
    text-align: center;
    background-color: #FAFAF9;
    min-height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.notebook-placeholder-text {
    font-family: 'EB Garamond', serif;
    font-style: italic;
    font-size: 15px;
    color: #90908C;
}
.notebook-canvas {
    border: 1.5px solid #121212;
    border-radius: 6px;
    padding: 1.5rem 2rem;
    min-height: 100px;
    margin-bottom: 1rem;
    background: #FFFFFF;
}
.notebook-formula {
    font-family: 'EB Garamond', serif;
    font-size: 18px;
    font-weight: 500;
    color: #121212;
    margin-bottom: 0.4rem;
}
.notebook-desc {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px;
    color: #5A5A57;
    line-height: 1.5;
}

.chat-mode-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #90908C;
    font-family: 'Plus Jakarta Sans', sans-serif;
    margin-bottom: 1.5rem;
    display: block;
}
.msg-wrapper { margin-bottom: 1.75rem; }
.msg-sender-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #90908C;
    margin-bottom: 0.35rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.msg-content-text {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    line-height: 1.65;
    color: #121212;
}
.msg-wrapper.system .msg-content-text {
    font-family: 'EB Garamond', serif !important;
    font-size: 15px !important;
    border-left: 1.5px solid #121212;
    padding-left: 0.85rem;
    line-height: 1.7;
}
.status-indicator {
    font-family: 'EB Garamond', serif;
    font-style: italic;
    color: #90908C;
    font-size: 13px;
    padding-left: 0.85rem;
    border-left: 1.5px solid #DEDAD5;
}

div[data-testid="stChatInput"] > div {
    background-color: #FFFFFF !important;
    border: none !important;
    border-bottom: 1.5px solid #121212 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 0.4rem 0 !important;
}
div[data-testid="stChatInput"] textarea {
    background-color: #FFFFFF !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 13px !important;
    color: #121212 !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
    color: #AEACA8 !important;
}
button[data-testid="stChatInputSubmit"] {
    background: none !important;
    border: none !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: #121212 !important;
    padding: 0 0 0 1rem !important;
    width: auto !important;
    height: auto !important;
    box-shadow: none !important;
}
button[data-testid="stChatInputSubmit"]:hover { opacity: 0.55 !important; }
button[data-testid="stChatInputSubmit"] svg { display: none !important; }
button[data-testid="stChatInputSubmit"]::after { content: "SEND" !important; display: block !important; }

div[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}
</style>
""", unsafe_allow_html=True)


# ── HEADER ───────────────────────────────────────────────────
now_str = dt.now().strftime("%b %-d · %-I:%M %p").upper()
st.markdown(f"""
<div class="ws-header">
    <span class="ws-brand">Physics Tutor</span>
    <span class="ws-timestamp">{now_str}</span>
</div>
""", unsafe_allow_html=True)


# ── GRID ─────────────────────────────────────────────────────
col_nav, col_workspace, col_spacer, col_chat = st.columns([0.07, 0.60, 0.08, 0.25])


# COLUMN 1: Navigation
with col_nav:
    st.markdown(
        f'<div class="sidebar-topic">{st.session_state.question_topic}</div>',
        unsafe_allow_html=True
    )
    c1, c2 = st.columns(2)
    with c1:
        st.button("Prev", key="btn_prev", on_click=lambda: navigate("prev"))
    with c2:
        st.button("Next", key="btn_next", on_click=lambda: navigate("next"))
    st.markdown(
        f'<div class="sidebar-id">ID {st.session_state.current_question_id}</div>',
        unsafe_allow_html=True
    )


# COLUMN 2: Problem Workspace
with col_workspace:
    st.markdown(
        f'<div class="problem-meta-label">Problem Unit {st.session_state.current_question_id}</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="problem-heading">Problem {st.session_state.current_question_id}</div>',
        unsafe_allow_html=True
    )
    st.markdown(st.session_state.question_context)

    if st.session_state.active_concept:
        st.markdown(clean_html(f"""
        <div class="active-concept-block">
            <div class="active-concept-label">Active Concept</div>
            <p class="active-concept-text">{st.session_state.active_concept}</p>
        </div>
        """), unsafe_allow_html=True)

    insight_count = len(st.session_state.insights)
    notebook_html = f"""
    <div class="notebook-wrapper">
        <div class="notebook-header-row">
            <span class="notebook-label">Study Notebook</span>
            <span class="notebook-count">{insight_count} Insight{"s" if insight_count != 1 else ""} Recorded</span>
        </div>
    """
    if not st.session_state.insights:
        notebook_html += """
        <div class="notebook-placeholder-box">
            <span class="notebook-placeholder-text">Awaiting formulas and insights from chat...</span>
        </div>
        """
    else:
        rendered_steps = set()
        for insight in st.session_state.insights:
            step_key = insight.get("step_key", "")
            if step_key in rendered_steps:
                continue
            rendered_steps.add(step_key)
            formula = insight.get("formula") or ""
            description = (
                insight.get("description") or insight.get("desc")
                or f"Successfully verified: {insight.get('theorem', 'Concept')}. Result: {insight.get('result', 'N/A')}."
            )
            notebook_html += f"""
            <div class="notebook-canvas">
                <div class="notebook-formula">{formula}</div>
                <div class="notebook-desc">{description}</div>
            </div>
            """
    notebook_html += "</div>"
    st.markdown(clean_html(notebook_html), unsafe_allow_html=True)


# COLUMN 3: Gutter
with col_spacer:
    pass


# COLUMN 4: Chat
with col_chat:
    mode_label = st.session_state.tutoring_mode.replace("Active — ", "").upper()
    st.markdown(f'<span class="chat-mode-label">{mode_label}</span>', unsafe_allow_html=True)

    chat_container = st.container(height=490, border=False)

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

    user_input = st.chat_input("Type logic or formula...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with chat_container:
            st.markdown(f"""
            <div class="msg-wrapper">
                <div class="msg-sender-label">You</div>
                <div class="msg-content-text">{user_input}</div>
            </div>
            """, unsafe_allow_html=True)
            status_placeholder = st.markdown(
                '<div class="status-indicator">Analyzing physics principles...</div>',
                unsafe_allow_html=True
            )
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
                    st.session_state.tutoring_mode = (
                        "Active — Socratic Mode" if backend_mode == "SOCRATIC" else "Active — Direct Mode"
                    )
                    nb_updates = data.get("notebook_updates", {})
                    if nb_updates and nb_updates.get("official_solution"):
                        st.session_state.insights.append(nb_updates["official_solution"])
                else:
                    ai_response = f"GCP Engine Error: code {response.status_code}."
            except Exception:
                status_placeholder.empty()
                ai_response = "GCP Synchronizer Error: unable to connect to API gateway."
            st.markdown(f"""
            <div class="msg-wrapper system">
                <div class="msg-sender-label">Socrates</div>
                <div class="msg-content-text">{ai_response}</div>
            </div>
            """, unsafe_allow_html=True)
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        st.rerun()
