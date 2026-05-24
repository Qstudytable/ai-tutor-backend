from fastapi import FastAPI, Request
from pydantic import BaseModel
from datetime import datetime, timezone
from security import InputValidator, UserIntent, SecurityFlag
from engine import ChronosEngine, PedagogyPhase
from llm import generate_transition_message, complete_tutor_turn

app = FastAPI()

# Data Models
class ChatRequest(BaseModel):
    user_text: str

class ChatResponse(BaseModel):
    ai_response: str
    phase: str
    is_correct: bool
    is_complete: bool
    focused_step: str | None

# In-Memory State for Investor Demo (Removes immediate MongoDB complexity)
demo_session = {
    "completed_steps": set(),
    "step_attempts": {},
    "current_focused_step": "step_1"
}

# Dummy Knowledge Graph for the Demo
steps_dict = {
    "step_1": {"formula": "F=ma", "theorem": "Newton's Second Law", "next": "step_2"},
    "step_2": {"formula": "v=u+at", "theorem": "Kinematics", "next": None}
}

def create_canned_response(message: str) -> ChatResponse:
    return ChatResponse(
        ai_response=message, phase=PedagogyPhase.SOCRATIC.value,
        is_correct=False, is_complete=False, focused_step=None
    )

@app.post("/chat/{session_id}", response_model=ChatResponse)
async def tutor_chat(request: Request, session_id: str, body: ChatRequest) -> ChatResponse:
    global demo_session
    now = datetime.now(timezone.utc)
    current_focus = demo_session["current_focused_step"]

    # ==========================================
    # PRE-CHECK: SECURITY & INTENT
    # ==========================================
    security_flag = await InputValidator.check_prompt_injection(body.user_text)
    if security_flag == SecurityFlag.JAILBREAK:
        return create_canned_response("I am a Physics Tutor AI. I cannot change my instructions.")
    elif security_flag == SecurityFlag.OFF_TOPIC:
        return create_canned_response("Let's stay focused on our physics problem. Where did you leave off?")
    elif security_flag == SecurityFlag.INAPPROPRIATE:
        return create_canned_response("Please keep the language appropriate and focused on learning.")

    intent = InputValidator.detect_shortcut_intent(body.user_text)
    if intent == UserIntent.EXPLICIT_HELP and current_focus:
        if demo_session["step_attempts"].get(current_focus, 0) < 3:
            demo_session["step_attempts"][current_focus] = 3

    # ==========================================
    # PHASE 1 & 2: DETERMINISTIC MATH EVALUATION
    # ==========================================
    matched_step = None
    if intent != UserIntent.EXPLICIT_HELP and current_focus:
        user_math_only = ChronosEngine.extract_math_from_text(body.user_text)
        expected_formula = steps_dict[current_focus]["formula"]
        
        is_correct, _ = ChronosEngine.verify_math(user_math_only, expected_formula)
        if is_correct:
            matched_step = current_focus

    if matched_step:
        demo_session["completed_steps"].add(matched_step)
        current_node = steps_dict[matched_step]
        new_focus = current_node["next"]
        demo_session["current_focused_step"] = new_focus
        
        next_theorem = steps_dict[new_focus]["theorem"] if new_focus else None
        ai_response = await generate_transition_message(current_node["theorem"], next_theorem)
        
        return ChatResponse(
            ai_response=ai_response, phase=PedagogyPhase.REVEAL.value,
            is_correct=True, is_complete=(new_focus is None), focused_step=new_focus
        )

    # ==========================================
    # PHASE 3: NO MATCH (LLM CHAT & ATTEMPT TRACKING)
    # ==========================================
    if intent != UserIntent.EXPLICIT_HELP and current_focus:
        demo_session["step_attempts"][current_focus] = demo_session["step_attempts"].get(current_focus, 0) + 1

    attempts = demo_session["step_attempts"].get(current_focus, 0)
    phase, phase_instruction = ChronosEngine.get_phase_context(attempts)
    
    ai_response = await complete_tutor_turn(body.user_text, phase_instruction)

    return ChatResponse(
        ai_response=ai_response, phase=phase.value,
        is_correct=False, is_complete=False, focused_step=current_focus
    )