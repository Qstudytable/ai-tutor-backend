import streamlit as st
import requests
import time
from datetime import datetime as dt

st.set_page_config(layout="wide", initial_sidebar_state="collapsed", page_title="Physics Tutor")

BACKEND_URL = "http://127.0.0.1:8000"

# --- STATE ---
defaults = {
    "session_id": None,
    "current_question_id": "00899",
    "chat_history": [{"role": "assistant", "content": "Welcome to the workspace. Let's step through this physics problem together. How can I help you resolve the active step?"}],
    "insights": [],
    "question_context": "",
    "question_title": "Physics Problem",
    "question_topic": "General Physics",
    "question_class": "Class 12",
    "question_subject": "Physics",
    "question_chapter": "General",
    "tutoring_mode": "Socratic Mode",
    "active_concept": "",
    "problem_slug": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def extract_metadata(data: dict):
    ctx = st.session_state.question_context.lower()
    topic = data.get("topic") or data.get("subject") or data.get("category") or (
        "Electromagnetic Induction" if any(w in ctx for w in ["magnetic","electromotive","induction","coil","flux"]) else
        "Classical Mechanics" if any(w in ctx for w in ["collides","velocity","mass","momentum","force"]) else
        "General Physics"
    )
    st.session_state.question_topic    = topic
    st.session_state.question_title    = data.get("title") or data.get("question_name") or f"Problem {st.session_state.current_question_id}"
    st.session_state.question_class    = data.get("class_level") or data.get("grade") or "Class 12"
    st.session_state.question_subject  = data.get("subject_name") or "Physics"
    st.session_state.question_chapter  = data.get("chapter") or topic
    st.session_state.active_concept    = data.get("active_concept") or data.get("key_concept") or data.get("concept") or ""
    st.session_state.problem_slug      = data.get("slug") or f"cal_problem_{st.session_state.current_question_id}"


def sync_session(session_id: str):
    try:
        res = requests.get(f"{BACKEND_URL}/session/{session_id}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.session_state.chat_history = data.get("chat_history") or st.session_state.chat_history
            st.session_state.insights     = data.get("notebook_history") or []
            mode = data.get("tutoring_mode", "socratic")
            st.session_state.tutoring_mode = "Socratic Mode" if mode == "socratic" else "Direct Mode"
            extract_metadata(data)
        else:
            st.error(f"Sync failed: {res.status_code}")
            st.stop()
    except Exception as e:
        st.error(f"Sync error: {e}")
        st.stop()


def init_session(q_id: str):
    url = f"{BACKEND_URL}/session/start/{q_id.strip()}"
    for attempt in range(10):
        try:
            res = requests.post(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                st.session_state.session_id          = data.get("session_id")
                st.session_state.current_question_id = data.get("question_id")
                st.session_state.question_context    = data.get("context", "")
                st.session_state.chat_history        = [{"role": "assistant", "content": "Welcome to the workspace. Let's step through this physics problem together. How can I help you resolve the active step?"}]
                st.session_state.insights            = []
                st.session_state.tutoring_mode       = "Socratic Mode"
                extract_metadata(data)
                return
            else:
                st.error(f"Init failed: {res.status_code}")
                st.stop()
        except requests.exceptions.ConnectionError:
            if attempt >= 3:
                st.warning(f"Connecting... ({attempt+1}/10)")
            time.sleep(3)
        except Exception as e:
            st.error(f"Init error: {e}")
            st.stop()
    st.error("Could not connect to backend.")
    st.stop()


def navigate(direction: str):
    try:
        res = requests.get(f"{BACKEND_URL}/questions/navigate/{st.session_state.current_question_id}/{direction}", timeout=5)
        if res.status_code == 200:
            nid = res.json().get("question_id")
            if nid:
                init_session(nid)
                st.rerun()
    except Exception as e:
        st.error(f"Navigation error: {e}")


# --- BOOT ---
if st.session_state.session_id is None:
    init_session(st.session_state.current_question_id)
else:
    sync_session(st.session_state.session_id)


def clean(html: str) -> str:
    return "\n".join(l.strip() for l in html.strip().split("\n"))


# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
.main, .block-container,
[data-testid="stVerticalBlock"] {
    background: #FFFFFF !important;
    color: #0D0D0D !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

header[data-testid="stHeader"], footer, #MainMenu { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── TOP NAV BAR ── */
.ws-nav {
    position: sticky;
    top: 0;
    z-index: 200;
    background: #FFFFFF;
    border-bottom: 1.5px solid #E8E6E1;
    height: 52px;
    display: flex;
    align-items: center;
    padding: 0 2.5%;
    gap: 0;
}
.ws-brand {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #0D0D0D;
    white-space: nowrap;
    margin-right: 3rem;
}
.ws-nav-center {
    display: flex;
    align-items: center;
    gap: 0;
    flex: 1;
    justify-content: center;
}
.ws-nav-btn {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #7A7875;
    cursor: pointer;
    padding: 0 1.2rem;
    text-decoration: none;
    transition: color 0.15s;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.ws-nav-btn:hover { color: #0D0D0D; }
.ws-nav-active {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #0D0D0D;
    padding: 0 1.2rem;
    border-bottom: 2px solid #0D0D0D;
    height: 52px;
    display: flex;
    align-items: center;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.ws-nav-right {
    display: flex;
    align-items: center;
    gap: 2rem;
    margin-left: 3rem;
}
.ws-nav-action {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #7A7875;
    cursor: pointer;
    font-family: 'Plus Jakarta Sans', sans-serif;
    transition: color 0.15s;
}
.ws-nav-action:hover { color: #0D0D0D; }

/* ── COLUMNS ── */
[data-testid="column"]:nth-of-type(1) {
    padding: 3.5rem 4% 3.5rem 5% !important;
    overflow-y: auto;
    height: calc(100vh - 52px);
    background: #FFFFFF;
    border-right: 1.5px solid #E8E6E1;
}
[data-testid="column"]:nth-of-type(2) {
    padding: 0 !important;
    height: calc(100vh - 52px);
    background: #FFFFFF;
    display: flex;
    flex-direction: column;
}

/* Kill Streamlit button default */
div.stButton > button {
    border: none !important;
    background: transparent !important;
    color: #7A7875 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    padding: 0 !important;
    line-height: 1 !important;
    height: auto !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    min-height: unset !important;
    width: auto !important;
}
div.stButton > button:hover { color: #0D0D0D !important; background: transparent !important; }
div.stButton > button:focus, div.stButton > button:active { box-shadow: none !important; border: none !important; outline: none !important; }

/* ── BREADCRUMB ── */
.breadcrumb {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9A9691;
    margin-bottom: 1.5rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.breadcrumb span { color: #C5C2BC; margin: 0 0.5rem; }

/* ── PROBLEM TITLE ── */
.prob-title {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 2.4rem;
    font-weight: 500;
    line-height: 1.15;
    color: #0D0D0D;
    letter-spacing: -0.02em;
    margin: 0 0 2rem 0;
}

/* ── PROBLEM BODY ── */
.prob-body {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 17px;
    line-height: 1.9;
    color: #1A1A1A;
    margin-bottom: 0;
}
.prob-body em, .prob-body i {
    font-style: italic;
}

/* Override Streamlit markdown paragraph */
[data-testid="column"]:nth-of-type(1) .stMarkdown p {
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 17px !important;
    line-height: 1.9 !important;
    color: #1A1A1A !important;
}

/* ── KEY CONCEPT ── */
.concept-block {
    border-left: 2.5px solid #0D0D0D;
    padding: 0.5rem 1.25rem 0.6rem;
    margin: 2rem 0 2.5rem 0;
}
.concept-label {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #9A9691;
    margin-bottom: 0.4rem;
}
.concept-text {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 16px;
    line-height: 1.75;
    color: #1A1A1A;
    margin: 0;
}

/* ── NOTEBOOK ── */
.notebook-section {
    margin-top: 3.5rem;
    padding-top: 0;
    border-top: 1.5px solid #E8E6E1;
}
.notebook-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem 0 1.25rem 0;
    border-bottom: 1px solid #F0EDE8;
    margin-bottom: 1.25rem;
}
.notebook-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #0D0D0D;
}
.notebook-count {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 11px;
    font-weight: 400;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #9A9691;
}
.notebook-card {
    border: 1.5px solid #E8E6E1;
    border-radius: 6px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.85rem;
    background: #FAFAF8;
    transition: border-color 0.2s;
}
.notebook-card:hover { border-color: #0D0D0D; }
.notebook-card-formula {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 19px;
    font-weight: 500;
    color: #0D0D0D;
    margin-bottom: 0.35rem;
}
.notebook-card-desc {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px;
    font-weight: 400;
    line-height: 1.55;
    color: #6A6762;
}

/* ── CHAT PANEL ── */
.chat-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
}
.chat-header {
    padding: 1.5rem 1.75rem 1rem;
    border-bottom: 1px solid #F0EDE8;
    flex-shrink: 0;
}
.chat-header-name {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #0D0D0D;
    text-transform: uppercase;
    margin-bottom: 0.2rem;
}
.chat-header-mode {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 11px;
    font-weight: 400;
    color: #9A9691;
}
.chat-header-divider {
    border: none;
    border-top: 1px solid #E8E6E1;
    margin: 1rem 0 0 0;
}

/* ── MESSAGES ── */
.msg-row { margin-bottom: 1.5rem; }
.msg-sender {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9A9691;
    margin-bottom: 0.4rem;
}
/* Socrates message: left-border serif */
.msg-socrates {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 15px;
    line-height: 1.75;
    color: #1A1A1A;
    border-left: 2px solid #0D0D0D;
    padding-left: 0.9rem;
}
/* User message: dark pill bubble */
.msg-you-wrap {
    display: flex;
    justify-content: flex-end;
}
.msg-you {
    background: #0D0D0D;
    color: #FFFFFF;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    line-height: 1.55;
    padding: 0.65rem 1rem;
    border-radius: 16px 16px 2px 16px;
    max-width: 85%;
    display: inline-block;
}
/* Processing italic */
.msg-processing {
    font-family: 'EB Garamond', Georgia, serif;
    font-style: italic;
    font-size: 14px;
    color: #9A9691;
    padding-left: 0.9rem;
    border-left: 2px solid #D8D5CF;
}

/* ── CHAT INPUT ── */
div[data-testid="stChatInput"] > div {
    background: #FFFFFF !important;
    border: none !important;
    border-top: 1.5px solid #E8E6E1 !important;
    border-bottom: 1.5px solid #0D0D0D !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 0.6rem 0 !important;
    margin: 0 1.75rem !important;
}
div[data-testid="stChatInput"] textarea {
    background: #FFFFFF !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 13px !important;
    color: #0D0D0D !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0.2rem 0 !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
    color: #B5B2AC !important;
    font-style: normal !important;
}
button[data-testid="stChatInputSubmit"] {
    background: none !important;
    border: none !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    color: #0D0D0D !important;
    padding: 0 0 0 0.75rem !important;
    box-shadow: none !important;
    transition: opacity 0.15s !important;
}
button[data-testid="stChatInputSubmit"]:hover { opacity: 0.4 !important; }
button[data-testid="stChatInputSubmit"] svg { display: none !important; }
button[data-testid="stChatInputSubmit"]::after { content: "SEND" !important; display: block !important; }

div[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Scrollbar ghost */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #E0DDD8; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)


# ── TOP NAV ──────────────────────────────────────────────────────────────────
slug = st.session_state.problem_slug or f"cal_problem_{st.session_state.current_question_id}"

# We render the brand + active slug + right actions in HTML,
# but PREV / NEXT need real Streamlit buttons — we layer them via columns inside the nav row.
st.markdown(f"""
<div class="ws-nav">
    <span class="ws-brand">Physics Tutor</span>
    <div class="ws-nav-center" id="nav-center-placeholder"></div>
    <div class="ws-nav-right">
        <span class="ws-nav-action">Upload</span>
        <span class="ws-nav-action">Exit</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Overlay PREV / slug / NEXT using a tight columns row placed immediately after header
nav_c1, nav_c2, nav_c3, nav_c4, nav_c5 = st.columns([0.18, 0.05, 0.14, 0.05, 0.58])
with nav_c1:
    pass
with nav_c2:
    st.button("Prev", key="btn_prev", on_click=lambda: navigate("prev"))
with nav_c3:
    st.markdown(f'<div class="ws-nav-active" style="justify-content:center;border-bottom:2px solid #0D0D0D;height:auto;padding:2px 0;">{slug}</div>', unsafe_allow_html=True)
with nav_c4:
    st.button("Next", key="btn_next", on_click=lambda: navigate("next"))
with nav_c5:
    pass


# ── MAIN GRID: workspace (65%) | chat (35%) ───────────────────────────────
col_ws, col_chat = st.columns([0.65, 0.35])


# ── WORKSPACE ────────────────────────────────────────────────────────────────
with col_ws:
    # Breadcrumb
    subject  = st.session_state.question_subject
    cls      = st.session_state.question_class
    chapter  = st.session_state.question_chapter
    st.markdown(
        f'<div class="breadcrumb">{subject}<span>/</span>{cls}<span>/</span>{chapter}</div>',
        unsafe_allow_html=True
    )

    # Title
    st.markdown(
        f'<div class="prob-title">Problem {st.session_state.current_question_id}</div>',
        unsafe_allow_html=True
    )

    # Problem text (rendered via st.markdown so LaTeX / bold / italic pass through)
    st.markdown(st.session_state.question_context)

    # Key Concept (only if backend provides it)
    if st.session_state.active_concept:
        st.markdown(clean(f"""
        <div class="concept-block">
            <div class="concept-label">Key Concept</div>
            <p class="concept-text">{st.session_state.active_concept}</p>
        </div>
        """), unsafe_allow_html=True)

    # ── STUDY NOTEBOOK ──
    insights = st.session_state.insights
    count    = len(insights)

    notebook_html = f"""
    <div class="notebook-section">
        <div class="notebook-header">
            <span class="notebook-title">Study Notebook</span>
            <span class="notebook-count">{count} Insight{"s" if count != 1 else ""} Recorded</span>
        </div>
    """
    if insights:
        seen = set()
        for ins in insights:
            key = ins.get("step_key", id(ins))
            if key in seen:
                continue
            seen.add(key)
            formula = ins.get("formula") or ""
            desc = (
                ins.get("description") or ins.get("desc")
                or f"Verified: {ins.get('theorem', 'Concept')} — result: {ins.get('result', 'N/A')}."
            )
            notebook_html += f"""
            <div class="notebook-card">
                <div class="notebook-card-formula">{formula}</div>
                <div class="notebook-card-desc">{desc}</div>
            </div>
            """
    # No placeholder when empty — just show the header row with 0 count
    notebook_html += "</div>"
    st.markdown(clean(notebook_html), unsafe_allow_html=True)


# ── CHAT PANEL ───────────────────────────────────────────────────────────────
with col_chat:
    mode = st.session_state.tutoring_mode
    st.markdown(f"""
    <div class="chat-header">
        <div class="chat-header-name">Socrates</div>
        <div class="chat-header-mode">Active — {mode}</div>
        <hr class="chat-header-divider"/>
    </div>
    """, unsafe_allow_html=True)

    chat_container = st.container(height=530, border=False)

    with chat_container:
        for msg in st.session_state.chat_history:
            is_assistant = msg["role"] in ["assistant", "tutor"]
            if is_assistant:
                st.markdown(f"""
                <div class="msg-row">
                    <div class="msg-sender">Socrates</div>
                    <div class="msg-socrates">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="msg-row" style="margin-left:auto;">
                    <div class="msg-sender" style="text-align:right;">You</div>
                    <div class="msg-you-wrap">
                        <div class="msg-you">{msg["content"]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    user_input = st.chat_input("Type your logic or formula...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with chat_container:
            st.markdown(f"""
            <div class="msg-row" style="margin-left:auto;">
                <div class="msg-sender" style="text-align:right;">You</div>
                <div class="msg-you-wrap">
                    <div class="msg-you">{user_input}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            status = st.markdown(
                '<div class="msg-processing">Socrates is processing...</div>',
                unsafe_allow_html=True
            )

            try:
                res = requests.post(
                    f"{BACKEND_URL}/chat/{st.session_state.session_id}",
                    json={"user_text": user_input},
                    timeout=15
                )
                status.empty()

                if res.status_code == 200:
                    data = res.json()
                    ai_resp = data.get("ai_response", "I'm having trouble analyzing this step.")
                    phase   = data.get("phase", "SOCRATIC")
                    st.session_state.tutoring_mode = "Socratic Mode" if phase == "SOCRATIC" else "Direct Mode"
                    nb = data.get("notebook_updates", {})
                    if nb and nb.get("official_solution"):
                        st.session_state.insights.append(nb["official_solution"])
                else:
                    ai_resp = f"Engine error: {res.status_code}."
            except Exception:
                status.empty()
                ai_resp = "Connection error: could not reach API gateway."

            st.markdown(f"""
            <div class="msg-row">
                <div class="msg-sender">Socrates</div>
                <div class="msg-socrates">{ai_resp}</div>
            </div>
            """, unsafe_allow_html=True)

        st.session_state.chat_history.append({"role": "assistant", "content": ai_resp})
        st.rerun()
