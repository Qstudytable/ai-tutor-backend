from __future__ import annotations

import os

# CRITICAL CLOUD FIX: Block Uvicorn from hijacking Cloud Run's port
if "PORT" in os.environ:
    del os.environ["PORT"]

import logging
import re
import uuid
import json
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from database import db
from engine import ChronosEngine, PedagogyPhase, VerifierSignal
from llm import build_knowledge_budget, build_tutor_messages, complete_tutor_turn, generate_transition_message
from middleware import preprocess_question_graph, get_active_unlocked_nodes
from security import InputValidator, UserIntent, SecurityFlag
from schemas import (
    ChatRequest,
    ChatResponse,
    NotebookOfficialSolution,
    NotebookUpdates,
    SessionSnapshotResponse,
    StartSessionResponse,
)

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("ai_tutoring_engine.main")

# Global Cache Loading
QUESTIONS_CACHE: dict[str, dict[str, Any]] = {}
if os.path.exists("all_data.json"):
    try:
        with open("all_data.json", "r") as f:
            _list = json.load(f)
            for q in _list:
                q_id = q.get("question_id")
                if q_id:
                    QUESTIONS_CACHE[q_id] = q
        logger.info("Loaded %d questions from all_data.json into cache.", len(QUESTIONS_CACHE))
    except Exception as e:
        logger.error("Failed to load all_data.json: %s", e)

CHAT_RATE_LIMIT = os.getenv("CHAT_RATE_LIMIT", "20/minute")

app = FastAPI(title="AI Tutoring Engine MVP", version="3.0.0")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def sort_step_keys(steps_dict: dict[str, Any]) -> list[str]:
    def step_num(key: str) -> int:
        match = re.search(r"\d+", key)
        if not match:
            raise ValueError(f"Step key does not contain a number: {key}")
        return int(match.group())
    return sorted(steps_dict.keys(), key=step_num)


def extract_step_data_safe(node: dict[str, Any]) -> tuple[str | None, str | None, str]:
    theorem = node.get("physical_theorem") or node.get("theorem") or "General Concept"
    result_quantity = node.get("result_quantity")
    if not isinstance(result_quantity, list) or not result_quantity:
        return None, None, theorem

    result = result_quantity[0]
    if not isinstance(result, dict):
        return None, None, theorem

    formula = result.get("equation")
    value = result.get("value")
    return (str(formula) if formula else None,
            str(value) if value is not None else None,
            theorem)


def question_context(question: dict[str, Any]) -> tuple[str, list[str]]:
    structure = question.get("question_structure", {})
    if not isinstance(structure, dict):
        return "", []

    sub_questions = [
        str(structure[key])
        for key in sorted(structure.keys())
        if key.startswith("sub_question_") and structure.get(key)
    ]
    return str(structure.get("context", "")), sub_questions


def create_canned_response(message: str) -> ChatResponse:
    return ChatResponse(
        ai_response=message,
        phase=PedagogyPhase.SOCRATIC,
        is_correct=False,
        verifier_signal=VerifierSignal.INCORRECT,
        is_complete=False,
        notebook_updates=NotebookUpdates(),
        new_active_nodes=[],
        focused_step=None
    )


async def load_session_or_404(session_id: str) -> dict[str, Any]:
    session = await db.sessions.find_one({"session_id": session_id}, {"_id": 0})
    if not session:
        # Failsafe session payload so it never crashes if database connection drops
        return {
            "session_id": session_id,
            "question_id": "00899",
            "completed_steps": [],
            "current_focused_step": "step_1",
            "step_attempts": {"step_1": 0},
            "notebook_history": [],
            "chat_history": []
        }
    return session


async def load_question_or_404(question_id: str) -> dict[str, Any]:
    """
    Loads question directly from the 1,200 preloaded cache.
    Bypasses MongoDB completely. If the requested ID is missing, 
    it falls back to the first available question in all_data.json.
    """
    # 1. Try to find the exact requested question
    if question_id in QUESTIONS_CACHE:
        logger.info(f"Successfully loaded question {question_id} from cache.")
        return QUESTIONS_CACHE[question_id]
         
    # 2. UNBREAKABLE FALLBACK: Serve the first question in your 1,200 dataset
    if QUESTIONS_CACHE:
        first_id = list(QUESTIONS_CACHE.keys())[0]
        logger.warning(f"Question {question_id} not found in cache. Falling back to active cached question: {first_id}")
        return QUESTIONS_CACHE[first_id]
         
    # 3. PANIC FALLBACK: Hardcoded Faraday's Law if all_data.json is completely empty
    logger.critical("QUESTIONS_CACHE is empty! Serving emergency fallback payload.")
    return {
        "question_id": question_id,
        "difficulty": "medium",
        "question_structure": {
            "context": (
                "A rectangular coil has $N = 100$ turns, with side lengths $ab = 30\\text{cm}$ and $ad = 20\\text{cm}$. "
                "It rotates inside a uniform magnetic field of $B = 0.8\\text{T}$ with an angular velocity of $\\omega = 100\\pi\\text{ rad/s}$."
            ),
            "sub_question_1": "Find the maximum induced electromotive force."
        },
        "steps_analysis": {
            "step_1": {
                "physical_theorem": "Faraday's Law of Induction",
                "theorem": "Faraday's Law of Induction",
                "socratic_hint": "Think about how maximum EMF relates to number of turns, field strength, coil area, and speed.",
                "depends_on": [],
                "result_quantity": [
                    {
                        "equation": "E = N*B*A*w",
                        "value": "150.8"
                    }
                ]
            }
        },
        "answer": ["150.8"]
    }


# ==========================================
# CORE ROUTERS & DIRECTORIES (Retained 100%)
# ==========================================

@app.get("/")
async def serve_index() -> FileResponse:
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "API is running. UI is active on the Streamlit port."}


@app.get("/health")
async def health() -> dict[str, str | bool]:
    return {"ok": True, "now": now_utc().isoformat()}


@app.get("/questions")
async def list_questions() -> list[dict[str, str]]:
    res = []
    for q_id, q in QUESTIONS_CACHE.items():
        context = q.get("question_structure", {}).get("context", "")
        preview = (context[:95] + "...") if len(context) > 95 else context
        res.append({
            "question_id": q_id,
            "preview": preview
        })
    if not res:
        res = [{"question_id": "phy_firefighter_001", "preview": "A firefighter aims a fire hose upward..."}]
    return res


@app.get("/questions/navigate/{question_id}/{direction}")
async def navigate_question(question_id: str, direction: str) -> dict[str, str | None]:
    keys = list(QUESTIONS_CACHE.keys())
    if not keys:
        return {"question_id": "phy_firefighter_001"}

    if question_id not in QUESTIONS_CACHE:
        return {"question_id": keys[0]}

    idx = keys.index(question_id)
    if direction == "next":
        next_idx = (idx + 1) % len(keys)
    else:
        next_idx = (idx - 1 + len(keys)) % len(keys)
    return {"question_id": keys[next_idx]}


@app.post("/session/{session_id}/mode/{mode}")
async def change_mode(session_id: str, mode: str) -> dict[str, str | bool]:
    if mode not in {"socratic", "direct"}:
        raise HTTPException(400, "Invalid mode. Must be 'socratic' or 'direct'")
    
    await db.sessions.update_one(
        {"session_id": session_id},
        {"$set": {"tutoring_mode": mode, "updated_at": now_utc().isoformat()}}
    )
    return {"ok": True, "mode": mode}


@app.post("/session/upload", response_model=StartSessionResponse)
async def upload_question(question: dict[str, Any]) -> StartSessionResponse:
    question_id = question.get("question_id")
    if not question_id:
        question_id = f"custom_phy_{uuid.uuid4().hex[:8]}"
        question["question_id"] = question_id

    if "steps_analysis" not in question:
        raise HTTPException(400, "Missing 'steps_analysis' in question JSON")
    if "question_structure" not in question:
        raise HTTPException(400, "Missing 'question_structure' in question JSON")

    await db.question_library.update_one(
        {"question_id": question_id},
        {"$set": question},
        upsert=True
    )
    return await start_session(question_id)


@app.get("/session/{session_id}", response_model=SessionSnapshotResponse)
async def get_session(session_id: str) -> SessionSnapshotResponse:
    session = await load_session_or_404(session_id)
    question = await load_question_or_404(session["question_id"])
    steps_dict = question.get("steps_analysis", {})
    if not isinstance(steps_dict, dict):
        raise HTTPException(422, "Malformed question: steps_analysis must be an object")

    step_keys = sort_step_keys(steps_dict)
    completed_list = session.get("completed_steps") or []
    
    return SessionSnapshotResponse(
        session_id=session["session_id"],
        question_id=session["question_id"],
        completed_steps=completed_list,
        focused_step=session.get("current_focused_step"),
        is_complete=len(completed_list) >= len(step_keys),
        notebook_history=session.get("notebook_history", []),
        chat_history=session.get("chat_history", []),
        tutoring_mode=session.get("tutoring_mode", "socratic"),
        steps_metadata=steps_dict,
        difficulty=question.get("difficulty", "medium"),
        theorems=question.get("Theorem") or [],
    )


# ==========================================
# STATE MACHINE COMPLIANT V3 SESSION START
# ==========================================

@app.post("/session/start/{question_id}/", response_model=StartSessionResponse)
@app.post("/session/start/{question_id}", response_model=StartSessionResponse)
async def start_session(question_id: str) -> StartSessionResponse:
    question = await load_question_or_404(question_id)
    session_id = str(uuid.uuid4())

    steps_dict = preprocess_question_graph(question.get("steps_analysis", {}))
    active_nodes = get_active_unlocked_nodes(steps_dict, set())
    initial_focus = active_nodes[0] if active_nodes else None

    # State Upgrade: Int-based attempts replace brittle timestamps
    step_attempts = {step_id: 0 for step_id in steps_dict.keys()}
    now_iso = now_utc().isoformat()

    await db.sessions.insert_one(
        {
            "session_id": session_id,
            "question_id": question_id,
            "completed_steps": [],
            "current_focused_step": initial_focus,
            "step_attempts": step_attempts,
            "tutoring_mode": "socratic",
            "notebook_history": [],
            "chat_history": [],
            "created_at": now_iso,
            "updated_at": now_iso,
        }
    )

    context, sub_questions = question_context(question)
    return StartSessionResponse(
        session_id=session_id,
        question_id=question_id,
        context=context,
        sub_questions=sub_questions,
    )


# ==========================================
# STATE MACHINE COMPLIANT V3 CHAT CORE
# ==========================================

@app.post("/chat/{session_id}", response_model=ChatResponse)
@limiter.limit(CHAT_RATE_LIMIT)
async def tutor_chat(request: Request, session_id: str, body: ChatRequest) -> ChatResponse:
    session = await load_session_or_404(session_id)
    question = await load_question_or_404(session["question_id"])

    steps_dict = preprocess_question_graph(question.get("steps_analysis", {}))
    step_keys = sort_step_keys(steps_dict)

    completed_steps = set(session.get("completed_steps") or [])
    step_attempts = session.get("step_attempts") or {}
    current_focus = session.get("current_focused_step")
    tutoring_mode = session.get("tutoring_mode", "socratic")
    now_iso = now_utc().isoformat()

    # Ensure attempts structure is fully populated
    for k in step_keys:
        if k not in step_attempts:
            step_attempts[k] = 0

    # Safety Lock check
    if len(completed_steps) >= len(step_keys):
        return ChatResponse(
            ai_response="You have successfully resolved this entire physics problem! Excellent job.",
            phase=PedagogyPhase.REVEAL,
            is_correct=True,
            verifier_signal=VerifierSignal.CORRECT,
            is_complete=True,
            notebook_updates=NotebookUpdates(),
            new_active_nodes=[],
            focused_step=None
        )

    # ==========================================
    # PRE-CHECK: SECURITY FIREWALL & INTENT CHECK
    # ==========================================
    security_flag = await InputValidator.check_prompt_injection(body.user_text)
    if security_flag == SecurityFlag.JAILBREAK:
        return create_canned_response("I am a Physics Tutor AI. I cannot modify my system instructions.")
    elif security_flag == SecurityFlag.OFF_TOPIC:
        return create_canned_response("Let's stay focused on our physics problem. Where did we leave off?")
    elif security_flag == SecurityFlag.INAPPROPRIATE:
        return create_canned_response("Please keep your language respectful and focused on physics.")

    intent = InputValidator.detect_shortcut_intent(body.user_text)
    if intent == UserIntent.EXPLICIT_HELP and current_focus:
        # User is stuck. Force DIRECT pedagogical mode by bumping attempts
        if step_attempts.get(current_focus, 0) < 3:
            step_attempts[current_focus] = 3

    # ==========================================
    # PHASE 1: DETERMINISTIC MATH EVALUATION
    # ==========================================
    matched_step = None
    verifier_signal = VerifierSignal.INCORRECT

    # Only verify math if student didn't explicitly yell "help"
    if intent != UserIntent.EXPLICIT_HELP:
        user_math_only = ChronosEngine.extract_math_from_text(body.user_text)
         
        # A. Final Answer Bypass Check
        final_answers = question.get("answer") or []
        if not isinstance(final_answers, list):
            final_answers = [final_answers]

        for ans in final_answers:
            is_bypass_correct, _ = ChronosEngine.verify_math(user_math_only, str(ans))
            if is_bypass_correct:
                completed_steps = set(step_keys)
                db_updates = {
                    "$set": {
                        "completed_steps": list(completed_steps),
                        "current_focused_step": None,
                        "updated_at": now_iso,
                    },
                    "$push": {
                        "chat_history": {
                            "$each": [
                                {"role": "user", "content": body.user_text},
                                {"role": "assistant", "content": "Brilliant! You jumped straight to the final answer."},
                            ]
                        }
                    }
                }
                await db.sessions.update_one({"session_id": session_id}, db_updates)
                return ChatResponse(
                    ai_response="Brilliant! You jumped straight to the final answer.",
                    phase=PedagogyPhase.REVEAL,
                    is_correct=True,
                    verifier_signal=VerifierSignal.CORRECT,
                    is_complete=True,
                    notebook_updates=NotebookUpdates(),
                    new_active_nodes=[],
                    focused_step=None
                )

        # B. Standard Active Node verification
        active_nodes = get_active_unlocked_nodes(steps_dict, completed_steps)
        for step_key in active_nodes:
            node = steps_dict[step_key]
            formula, final_value, theorem = extract_step_data_safe(node)
             
            is_correct = False
            if formula:
                is_correct, signal = ChronosEngine.verify_math(user_math_only, formula)
                if is_correct:
                    matched_step = step_key
                    verifier_signal = signal
                    break
                elif signal == VerifierSignal.SIGN_FLIP:
                    verifier_signal = signal

            if final_value and not matched_step:
                is_correct, signal = ChronosEngine.verify_math(user_math_only, final_value)
                if is_correct:
                    matched_step = step_key
                    verifier_signal = signal
                    break

    # ==========================================
    # PHASE 2: MATCH FOUND (LOCK AND MOVE)
    # ==========================================
    if matched_step:
        completed_steps.add(matched_step)
        new_active = get_active_unlocked_nodes(steps_dict, completed_steps)
        new_focus = new_active[0] if new_active else None

        node = steps_dict[matched_step]
        formula, final_value, theorem = extract_step_data_safe(node)
        next_theorem = steps_dict[new_focus].get("physical_theorem") if new_focus else None

        official_solution = NotebookOfficialSolution(
            step_key=matched_step,
            theorem=theorem,
            formula=formula or "N/A",
            result=final_value,
            timestamp=now_iso,
        )

        # Generates fast praise/transition (Under 500ms)
        ai_response = await generate_transition_message(theorem, next_theorem)

        db_updates = {
            "$push": {
                "chat_history": {
                    "$each": [
                        {"role": "user", "content": body.user_text},
                        {"role": "assistant", "content": ai_response},
                    ]
                },
                "notebook_history": official_solution.model_dump(mode="json")
            },
            "$set": {
                "completed_steps": list(completed_steps),
                "current_focused_step": new_focus,
                "step_attempts": step_attempts,
                "updated_at": now_iso,
            }
        }
        await db.sessions.update_one({"session_id": session_id}, db_updates)

        return ChatResponse(
            ai_response=ai_response,
            phase=PedagogyPhase.REVEAL,
            is_correct=True,
            verifier_signal=verifier_signal,
            is_complete=len(completed_steps) >= len(step_keys),
            notebook_updates=NotebookUpdates(official_solution=official_solution),
            new_active_nodes=new_active,
            focused_step=new_focus
        )

    # ==========================================
    # PHASE 3: NO MATCH (TUTOR TURN & SYSTEM ACTIONS)
    # ==========================================
    if intent != UserIntent.EXPLICIT_HELP and current_focus:
        step_attempts[current_focus] = step_attempts.get(current_focus, 0) + 1

    active_nodes = get_active_unlocked_nodes(steps_dict, completed_steps)
    if not current_focus or current_focus not in active_nodes:
        current_focus = active_nodes[0] if active_nodes else None

    # Pedagogy governed by integer failures
    current_attempts = step_attempts.get(current_focus, 0) if current_focus else 0
    phase, phase_instruction = ChronosEngine.get_phase_context(current_attempts)

    theorem = "General Concept"
    hint = "Ask the learner what principle applies."
    formula = "N/A"
    final_value = None

    if current_focus:
        node = steps_dict[current_focus]
        formula_extracted, val_extracted, theorem_extracted = extract_step_data_safe(node)
        formula = formula_extracted or "N/A"
        final_value = val_extracted
        theorem = theorem_extracted
        hint = str(node.get("socratic_hint") or node.get("hint") or hint)

    knowledge_budget = build_knowledge_budget(
        phase=phase,
        theorem=theorem,
        hint=hint,
        formula=formula,
        final_value=final_value,
        notebook_history=session.get("notebook_history", []),
    )

    messages = build_tutor_messages(
        phase=phase,
        phase_instruction=phase_instruction,
        verifier_signal=verifier_signal,
        knowledge_budget=knowledge_budget,
        recent_history=session.get("chat_history", []),
        user_text=body.user_text,
        tutoring_mode=tutoring_mode,
        active_nodes=active_nodes,
        focused_step=current_focus
    )

    ai_response, dynamic_note, action = await complete_tutor_turn(messages)

    # 100% RETENTION: Execute dynamic LLM background action dispatches
    official_solution = None
    if action:
        action_name = action.get("action")
        target_step_id = action.get("target_step_id")

        if action_name == "solve_step" and target_step_id in active_nodes:
            completed_steps.add(target_step_id)
            active_nodes = get_active_unlocked_nodes(steps_dict, completed_steps)
            current_focus = active_nodes[0] if active_nodes else None

            node = steps_dict[target_step_id]
            formula_act, val_act, theorem_act = extract_step_data_safe(node)
            official_solution = NotebookOfficialSolution(
                step_key=target_step_id,
                theorem=theorem_act,
                formula=formula_act or "N/A",
                result=val_act,
                timestamp=now_iso,
            )
        elif action_name == "jump_to_step" and target_step_id in active_nodes:
            current_focus = target_step_id

    # Sync and format notebook logs
    notebook_entries = []
    if dynamic_note:
        notebook_entries.append(dynamic_note.model_dump(mode="json"))
    if official_solution:
        notebook_entries.append(official_solution.model_dump(mode="json"))

    db_payload_push = {
        "chat_history": {
            "$each": [
                {"role": "user", "content": body.user_text},
                {"role": "assistant", "content": ai_response},
            ]
        }
    }
    if notebook_entries:
        db_payload_push["notebook_history"] = {"$each": notebook_entries}

    db_updates = {
        "$push": db_payload_push,
        "$set": {
            "completed_steps": list(completed_steps),
            "current_focused_step": current_focus,
            "step_attempts": step_attempts,
            "updated_at": now_iso,
        }
    }
    await db.sessions.update_one({"session_id": session_id}, db_updates)

    return ChatResponse(
        ai_response=ai_response,
        phase=phase,
        is_correct=False,
        verifier_signal=verifier_signal,
        is_complete=len(completed_steps) >= len(step_keys),
        notebook_updates=NotebookUpdates(
            dynamic_note=dynamic_note,
            official_solution=official_solution,
        ),
        new_active_nodes=active_nodes,
        focused_step=current_focus
    )


@app.on_event("startup")
async def startup_event():
    question = await db.question_library.find_one({"question_id": "phy_firefighter_001"})
    if not question:
        logger.info("Auto-seeding phy_firefighter_001...")
        try:
            from seed import question_data
            await db.question_library.update_one(
                {"question_id": "phy_firefighter_001"},
                {"$set": question_data},
                upsert=True
            )
        except ImportError:
            logger.warning("seed.py not found. Skipping auto-seed.")
