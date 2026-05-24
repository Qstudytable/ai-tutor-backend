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


# Rebuilds state if the student refreshes the browser page
def sync_session_snapshot(session_id: str):
    try:
        res = requests.get(f"{BACKEND_URL}/session/{session_id}", timeout=3)
        if res.status_code == 200:
            data = res.json()
            st.session_state.chat_history = data.get("chat_history") or []
            st.session_state.insights = data.get("notebook_history") or []
    except Exception:
        pass


# Starts a brand-new session on the backend
def init_session(q_id: str):
    try:
        res = requests.post(f"{BACKEND_URL}/session/start/{q_id}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.session_state.session_id = data.get("session_id")
            st.session_state.current_question_id = data.get("question_id")
            st.session_state.question_context = data.get("context")
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Welcome. I'm ready to help you work through this physics problem. Where would you like to start?"}
            ]
            st.session_state.insights = []
    except Exception:
        # Robust offline fallback for local investor demo simulations
        st.session_state.session_id = f"demo_fallback_{q_id}"
        st.session_state.current_question_id = q_id
        st.session_state.question_context = "A rectangular coil has N = 100 turns, with side lengths ab = 30cm and ad = 20cm rotating inside field..."
        st.session_state.chat_history = [
            {"role": "assistant", "content": f"[DEMO RUN] Loaded offline fallback mode for Question {q_id}."}
        ]
        st.session_state.insights = []


# --- DYNAMIC BACKEND NAVIGATION ---
def navigate(direction: str):
    try:
        # Asks main.py which question ID sits in the specified direction
        res = requests.get(f"{BACKEND_URL}/questions/navigate/{st.session_state.current_question_id}/{direction}", timeout=3)
        if res.status_code == 200:
            next_q_id = res.json().get("question_id")
            if next_q_id:
                init_session(next_q_id)
    except Exception:
        # Static local navigation fallback if backend connection drops
        fallback_playlist = ["00899", "phy_firefighter_001"]
        try:
            curr_idx = fallback_playlist.index(st.session_state.current_question_id)
            new_idx = (curr_idx + 1) % len(fallback_playlist) if direction == "next" else (curr_idx - 1) % len(fallback_playlist)
            init_session(fallback_playlist[new_idx])
        except ValueError:
            init_session(fallback_playlist[0])


# Execute initial startup routine if none exists
if st.session_state.session_id is None:
    init_session(st.session_state.current_question_id)
else:
    # Attempt to sync up any background updates
    if not st.session_state.session_id.startswith("demo_fallback_"):
        sync_session_snapshot(st.session_state.session_id)


# --- APPLE-STYLE TYPOGRAPHY DESIGN ---
st.markdown(textwrap.dedent("""
<style>
  html, body, [data-testid="stAppViewContainer"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: #FFFFFF;
    color: #1D1D1F;
  }
  
  header, footer, #MainMenu { display: none !important; }
  .block-container { padding: 3rem 5rem !important; max-width: 100% !important; }
  
  .sys-time { font-size: 0.85rem; font-weight: 500; color: #86868B; letter-spacing: 0.04em; }

  /* Chat Bubble selectors targeting native Streamlit wrappers cleanly */
  div[data-testid="stChatMessage"] {
    background-color: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-radius: 16px !important;
    padding: 12px 18px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.01);
    margin-bottom: 0.8rem;
  }
  div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageHeader"]:contains("user")) {
    background-color: #F5F5F7 !important;
    border: none !important;
  }
  
  .tag { font-size: 0.75rem; font-weight: 600; color: #86868B; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 12px; }
  .title { font-size: 2.2rem; font-weight: 600; letter-spacing: -0.02em; color: #1D1D1F; margin-bottom: 24px; }
  .active-task { background-color: #F5F5F7; border-radius: 12px; padding: 20px; border-left: 4px solid #1D1D1F; font-size: 1.05rem; line-height: 1.6; }
  
  /* Study Notebook components */
  .notebook-section { margin-top: 3rem; border-top: 1px solid #E5E5EA; padding-top: 2rem; }
  .notebook-header { font-size: 0.85rem; font-weight: 600; color: #1D1D1F; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 1.5rem; }
  .notebook-card { background-color: #FFFFFF; border-radius: 12px; padding: 18px; margin-bottom: 14px; border: 1px solid #E5E5EA; transition: all 0.2s ease; }
  .notebook-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
  .card-label { font-size: 0.72rem; font-weight: 600; color: #86868B; text-transform: uppercase; letter-spacing: 0.04em; }
  .card-value { font-family: ui-monospace, SFMono-Regular, monospace; font-size: 1.15rem; color: #1D1D1F; margin-top: 6px; }

  /* Custom Rounded Buttons */
  [data-testid="stButton"] button { border-radius: 24px; border: 1px solid #E5E5EA; background: #FFFFFF; color: #1D1D1F; font-weight: 500; transition: all 0.2s ease; }
  [data-testid="stButton"] button:hover { background: #F5F5F7; border-color: #D2D2D7; }
</style>
"""), unsafe_allow_html=True)


# --- UI HEADER TIME ---
now_dt = dt.now()
time_str = now_dt.strftime("%A, %B %d | %I:%M %p").upper()

st.markdown(f'<div class="sys-time">{time_str}</div>', unsafe_allow_html=True)
st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)

h_col1, h_col2, h_col3 = st.columns([1, 10, 1])
with h_col1:
    st.button("← Prev", on_click=lambda: navigate("prev"), use_container_width=True)
with h_col3:
    st.button("Next →", on_click=lambda: navigate("next"), use_container_width=True)

st.markdown('<div style="border-bottom: 1px solid #E5E5EA; margin-bottom: 2rem;"></div>', unsafe_allow_html=True)


# --- SPLIT LAYOUT SPLIT ---
left_col, right_col = st.columns([5.5, 4.5], gap="large")

# ==========================================
# LEFT PANEL: CONTEXT & DURABLE NOTEBOOK
# ==========================================
with left_col:
    st.markdown('<div class="tag">Physics · Electromagnetic Induction</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="title">Problem {st.session_state.current_question_id}</div>', unsafe_allow_html=True)
    
    # Native markdown wrapper displays high-resolution KaTeX rendering correctly
    st.markdown(st.session_state.question_context)
    st.write("")

    st.markdown("""
    <div class="active-task">
        <strong>Active Task:</strong> Apply Faraday's law of electromagnetic induction to find the maximum induced electromotive force in a rotating coil.
    </div>
    """, unsafe_allow_html=True)
     
    st.markdown('<div class="notebook-section"><div class="notebook-header">Study Notebook</div>', unsafe_allow_html=True)
    
    if not st.session_state.insights:
        st.markdown('<div style="color: #86868B; font-style: italic; font-size: 0.95rem;">No insights recorded yet. Talk to the tutor to begin unlocking steps.</div>', unsafe_allow_html=True)
    else:
        for idx, insight in enumerate(st.session_state.insights):
            st.markdown(f"""
            <div class="notebook-card">
                <div class="card-label">{insight.get('theorem', 'Physics Principle')}</div>
                <div class="card-value">{insight.get('formula', '')}</div>
                <div style="font-size: 0.85rem; color: #86868B; margin-top: 8px;">Calculated value: {insight.get('result', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# RIGHT PANEL: AI CHAT WORKSPACE
# ==========================================
with right_col:
    # Native scroll container auto-scrolls correctly and retains css overrides
    chat_container = st.container(height=520, border=False)
    
    with chat_container:
        for msg in st.session_state.chat_history:
            role = "user" if msg["role"] == "You" or msg["role"] == "user" else "assistant"
            with st.chat_message(role):
                st.write(msg["content"])
                
    user_input = st.chat_input("Message Tutor...")
    
    if user_input:
        st.session_state.chat_history.append({"role": "You", "content": user_input})
        
        with chat_container:
            with st.chat_message("user"):
                st.write(user_input)
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/chat/{st.session_state.session_id}",
                            json={"user_text": user_input},
                            timeout=15
                        )
                        if response.status_code == 200:
                            data = response.json()
                            ai_response = data.get("ai_response", "I'm having trouble analyzing this step.")
                            
                            nb_updates = data.get("notebook_updates", {})
                            if nb_updates and nb_updates.get("official_solution"):
                                st.session_state.insights.append(nb_updates["official_solution"])
                        else:
                            ai_response = "System error: Feedback loop disrupted."
                    except Exception:
                        ai_response = "API synchronization in progress. Please hold."
                
                st.write(ai_response)
        
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        st.rerun()
