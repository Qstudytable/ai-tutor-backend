import streamlit as st
import requests
from datetime import datetime

# 1. Page Configuration (Must be wide to match your design)
st.set_page_config(layout="wide", page_title="Physics Tutor", page_icon="⚛️", initial_sidebar_state="collapsed")

# 2. Injecting Custom CSS to match your exact design
st.markdown("""
<style>
    /* Hide default Streamlit headers and footers to make it look like a real app */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Adjust main padding */
    .block-container {
        padding-top: 1rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        max-width: 100% !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Top Navigation Bar */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #eaeaea;
        padding-bottom: 15px;
        margin-bottom: 30px;
        color: #111;
        font-family: 'Inter', sans-serif;
    }
    .top-nav .logo { font-weight: 700; font-size: 0.9rem; letter-spacing: 1.5px; }
    .top-nav .date { font-size: 0.8rem; color: #666; letter-spacing: 1px; }

    /* Active Concept Block */
    .active-concept {
        border-left: 3px solid #111;
        padding-left: 20px;
        margin: 30px 0;
    }
    .concept-label {
        font-size: 0.75rem;
        font-weight: 700;
        color: #666;
        letter-spacing: 1.2px;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .concept-text {
        font-size: 1.1rem;
        color: #222;
        line-height: 1.5;
        font-family: 'Georgia', serif; /* Gives that academic textbook feel */
    }

    /* Study Notebook */
    .notebook-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        margin-top: 50px;
        margin-bottom: 10px;
    }
    .notebook-title { font-size: 0.8rem; font-weight: 700; letter-spacing: 1.2px; }
    .notebook-count { font-size: 0.8rem; color: #999; }
    
    .notebook-box {
        border: 1px solid #eaeaea;
        border-radius: 8px;
        background-color: #fafafa;
        padding: 120px 20px;
        text-align: center;
        color: #888;
        font-style: italic;
    }

    /* Chat Area Styling */
    .socratic-mode-label {
        text-align: center;
        font-size: 0.75rem;
        font-weight: 700;
        color: #888;
        letter-spacing: 1.5px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Top Navigation Bar
current_date = datetime.now().strftime("%b %d").upper()
st.markdown(f"""
<div class="top-nav">
    <div class="logo">PHYSICS TUTOR</div>
    <div class="date">{current_date} · ACTIVE SESSION</div>
</div>
""", unsafe_allow_html=True)

# 4. Create the Split Layout (Left: 60%, Right: 40%)
col1, padding, col2 = st.columns([1.6, 0.1, 1])

# ==========================================
# LEFT COLUMN (Problem & Notebook)
# ==========================================
with col1:
    # Subtitle
    st.markdown("<div style='color: #888; font-size: 0.8rem; font-weight: 600; letter-spacing: 1px; margin-bottom: 10px;'>CLASS 12 · ELECTROMAGNETIC INDUCTION</div>", unsafe_allow_html=True)
    
    # Title
    st.markdown("<h1 style='margin-top: 0; padding-top: 0; font-size: 2rem; color: #111;'>Problem 00899</h1>", unsafe_allow_html=True)
    st.write("") # Spacer

    # Problem Text (With LaTeX rendering exactly like your image)
    st.markdown("""
    <div style='font-size: 1.15rem; line-height: 1.8; color: #111; font-family: Georgia, serif;'>
    A rectangular coil has $N = 100$ turns, with side lengths $ab = 30cm$ and $ad = 20cm$. 
    It is placed in a uniform magnetic field with a magnetic induction strength of $B = 0.8T$. 
    The coil rotates uniformly about the axis O' starting from the position shown in the diagram, 
    with an angular velocity of $\\omega = 100\\pi$ rad/s.
    </div>
    """, unsafe_allow_html=True)

    # Active Concept Block
    st.markdown("""
    <div class="active-concept">
        <div class="concept-label">Active Concept</div>
        <div class="concept-text">Apply Faraday's law of electromagnetic induction to find the maximum induced electromotive force in a rotating coil.</div>
    </div>
    """, unsafe_allow_html=True)

    # Study Notebook Area
    notebook_insights = st.session_state.get("notebook_insights", 0)
    st.markdown(f"""
    <div class="notebook-header">
        <div class="notebook-title">STUDY NOTEBOOK</div>
        <div class="notebook-count">{notebook_insights} Insights Recorded</div>
    </div>
    <div class="notebook-box">
        Awaiting formulas and insights from chat...
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# RIGHT COLUMN (Socratic Chat Interface)
# ==========================================
with col2:
    st.markdown("<div class='socratic-mode-label'>SOCRATIC MODE</div>", unsafe_allow_html=True)
    
    # Initialize chat history if empty
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome to the workspace. Let's step through this physics problem together. How can I help you resolve the active step?"},
            {"role": "user", "content": "What is the basic concept?"}
        ]

    # Create a scrollable container for chat messages
    chat_container = st.container(height=600, border=False)
    
    with chat_container:
        for msg in st.session_state.messages:
            # We rename 'assistant' to 'Socrates' for the UI display
            avatar = "🎓" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # Chat Input Box at the bottom
    user_input = st.chat_input("Type logic or formula...")

    if user_input:
        # 1. Add User message to UI
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_container:
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)
            
            # 2. Add typing indicator
            with st.chat_message("assistant", avatar="🎓"):
                with st.spinner("Analyzing physics principles..."):
                    try:
                        # 3. Call your FastAPI backend!
                        # (Matches the main.py server running on port 8000)
                        res = requests.post(
                            "http://127.0.0.1:8000/chat/demo123", 
                            json={"user_text": user_input}
                        )
                        if res.status_code == 200:
                            data = res.json()
                            response_text = data["ai_response"]
                        else:
                            response_text = "I'm having trouble connecting to the logic engine."
                    except Exception as e:
                        response_text = "Backend is starting up, please hold on..."

                # 4. Show AI response
                st.markdown(response_text)
                
        # 5. Save AI response to session state
        st.session_state.messages.append({"role": "assistant", "content": response_text})