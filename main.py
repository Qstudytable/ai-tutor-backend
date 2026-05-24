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
from llm import build_knowledge_budget, build_tutor_messages, complete_tutor_turn
from middleware import preprocess_question_graph, get_active_unlocked_nodes
from schemas import (
    ChatRequest,
    ChatResponse,
    NotebookOfficialSolution,
    NotebookUpdates,
    SessionSnapshotResponse,
    StartSessionResponse,
)

load_dotenv()

# We won't crash the build if the key is missing yet, 
# it will be provided by Google Cloud Secrets manager later.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("ai_tutoring_engine")

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

CHAT_RATE_LIMIT = os.getenv("CHAT_RATE_LIMIT", "10/minute")

app = FastAPI(title="AI Tutoring Engine MVP")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Only mount static if the directory actually exists to prevent crashes
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index() -> FileResponse:
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "API is running. UI is at the Streamlit port."}

@app.post("/session/{session_id}/mode/{mode}")
async def change_mode(session_id: str, mode: str) -> dict[str, str | bool]:
    if mode not in {"socratic", "direct"}:
        raise HTTPException(400, "Invalid mode. Must be 'socratic' or 'direct'")
    
    await db.sessions.update_one(
        {"session_id": session_id},
        {"$set": {"tutoring_mode": mode, "updated_at": now_utc()}}
    )
    return {"ok": True, "mode": mode}

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


async def load_session_or_404(session_id: str) -> dict[str, Any]:
    session = await db.sessions.find_one({"session_id": session_id}, {"_id": 0})
    if not session:
        # Failsafe for the investor demo so it never crashes if DB resets
        return {
            "session_id": session_id,
            "question_id": "00899",
            "step_idx": 0,
            "start_time": now_utc().isoformat(),
            "notebook_history": [],
            "chat_history": []
        }
    return session


async def load_question_or_404(question_id: str) -> dict[str, Any]:
    if question_id in QUESTIONS_CACHE:
        return QUESTIONS_CACHE[question_id]
    question = await db.question_library.find_one({"question_id": question_id}, {"_id": 0})
    if not question:
        # Investor Demo Failsafe for Problem 00899
        return {
            "question_id": question_id,
            "question_structure": {"context": "A rectangular coil in a magnetic field..."},
            "steps_analysis": {
                "step_1": {"formula": "E = N*B*A*w", "final_value": "15.08", "theorem": "Faraday's Law of Induction"}
            }
        }
    return question


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


@app.post("/session/start/{question_id}", response_model=StartSessionResponse)
async def start_session(question_id: str) -> StartSessionResponse:
    question = await load_question_or_404(question_id)
    session_id = str(uuid.uuid4())

    steps_dict = preprocess_question_graph(question.get("steps_analysis", {}))
    active_nodes = get_active_unlocked_nodes(steps_dict, set())
    initial_focus = active_nodes[0] if active_nodes else None

    now = now_utc()
    step_start_times = {step_id: now.isoformat() for step_id in steps_dict.keys()}

    await db.sessions.insert_one(
        {
            "session_id": session_id,
            "question_id": question_id,
            "completed_steps": [],
            "current_focused_step": initial_focus,
            "step_start_times": step_start_times,
            "tutoring_mode": "socratic",
            "notebook_history": [],
            "chat_history": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
    )

    context, sub_questions = question_context(question)
    return StartSessionResponse(
        session_id=session_id,
        question_id=question_id,
        context=context,
        sub_questions=sub_questions,
    )


@app.get("/session/{session_id}", response_model=SessionSnapshotResponse)
async def get_session(session_id: str) -> SessionSnapshotResponse:
    session = await load_session_or_404(session_id)
    question = await load_question_or_404(session["question_id"])
    steps_dict = question.get("steps_analysis", {})
    if not isinstance(steps_dict, dict):
        raise HTTPException(422, "Malformed question: steps_analysis must be an object")

    step_keys = sort_step_keys(steps_dict)
    completed_list = session.get("completed_steps") or []
    
    # Handle missing timestamps
    start_time_str = session.get("start_time", now_utc().isoformat())
    if isinstance(start_time_str, datetime):
        start_time_str = start_time_str.isoformat()
        
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


@app.post("/chat/{session_id}", response_model=ChatResponse)
@limiter.limit(CHAT_RATE_LIMIT)
async def tutor_chat(request: Request, session_id: str, body: ChatRequest) -> ChatResponse:
    session = await load_session_or_404(session_id)
    question = await load_question_or_404(session["question_id"])

    steps_dict = preprocess_question_graph(question.get("steps_analysis", {}))
    step_keys = sort_step_keys(steps_dict)

    completed_list = session.get("completed_steps") or []
    completed_steps = set(completed_list)
    tutoring_mode = session.get("tutoring_mode", "socratic")
    step_start_times = session.get("step_start_times") or {}

    now = now_utc()
    now_iso = now.isoformat()
    # Normalize step_start_times
    for k in step_keys:
        if k not in step_start_times:
            step_start_times[k] = now_iso

    is_complete = len(completed_steps) >= len(step_keys)
    if is_complete:
        return ChatResponse(
            ai_response="You've already finished this problem.",
            phase=PedagogyPhase.REVEAL,
            is_correct=True,
            verifier_signal=VerifierSignal.CORRECT,
            is_complete=True,
            notebook_updates=NotebookUpdates(),
            new_active_nodes=[],
            focused_step=None
        )

    # --- PHASE 1: DETERMINISTIC MATH EVALUATION ---

    # A. Final Answer Bypass
    final_answers = question.get("answer") or []
    if not isinstance(final_answers, list):
        final_answers = [final_answers]

    for ans in final_answers:
        is_bypass_correct, _ = ChronosEngine.verify_math(body.user_text, str(ans))
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

    # B. Parallel Active Step Check
    active_nodes = get_active_unlocked_nodes(steps_dict, completed_steps)
    matched_step = None
    verifier_signal = VerifierSignal.INCORRECT

    for step_key in active_nodes:
        node = steps_dict[step_key]
        formula, final_value, theorem = extract_step_data_safe(node)
        
        is_correct = False
        if formula:
            is_correct, signal = ChronosEngine.verify_math(body.user_text, formula)
            if is_correct:
                matched_step = step_key
                verifier_signal = signal
                break
            elif signal == VerifierSignal.SIGN_FLIP:
                verifier_signal = signal

        if final_value and not matched_step:
            is_correct, signal = ChronosEngine.verify_math(body.user_text, final_value)
            if is_correct:
                matched_step = step_key
                verifier_signal = signal
                break

    if matched_step:
        completed_steps.add(matched_step)
        new_active = get_active_unlocked_nodes(steps_dict, completed_steps)
        new_focus = new_active[0] if new_active else None
        
        # Reset timers for newly unlocked steps
        for step in new_active:
            if step not in completed_steps:
                step_start_times[step] = now.isoformat()

        node = steps_dict[matched_step]
        formula, final_value, theorem = extract_step_data_safe(node)
        official_solution = NotebookOfficialSolution(
            step_key=matched_step,
            theorem=theorem,
            formula=formula or "N/A",
            result=final_value,
            timestamp=now_iso,
        )

        ai_response = f"Correct! You solved the step: {theorem}."
        push_payload = {
            "chat_history": {
                "$each": [
                    {"role": "user", "content": body.user_text},
                    {"role": "assistant", "content": ai_response},
                ]
            },
            "notebook_history": official_solution.model_dump(mode="json")
        }

        db_updates = {
            "$push": push_payload,
            "$set": {
                "completed_steps": list(completed_steps),
                "current_focused_step": new_focus,
                "step_start_times": step_start_times,
                "updated_at": now_iso,
            }
        }
        await db.sessions.update_one({"session_id": session_id}, db_updates)

        is_complete_now = len(completed_steps) >= len(step_keys)
        return ChatResponse(
            ai_response=ai_response,
            phase=PedagogyPhase.REVEAL,
            is_correct=True,
            verifier_signal=verifier_signal,
            is_complete=is_complete_now,
            notebook_updates=NotebookUpdates(official_solution=official_solution),
            new_active_nodes=new_active,
            focused_step=new_focus
        )

    # --- PHASE 2: LLM CHAT / NAVIGATION ENGINE ---
    current_focus = session.get("current_focused_step")
    if not current_focus or current_focus not in active_nodes:
        current_focus = active_nodes[0] if active_nodes else None

    phase = PedagogyPhase.SOCRATIC
    phase_instruction = "Ask guiding questions. Maximum of two lines is allowed. Do not give formulas, substitutions, final values, or the answer."
    if current_focus:
        focus_start_str = step_start_times.get(current_focus)
        if focus_start_str:
            try:
                focus_start = datetime.fromisoformat(focus_start_str)
                if focus_start.tzinfo is None:
                    focus_start = focus_start.replace(tzinfo=timezone.utc)
                phase, phase_instruction = ChronosEngine.get_phase_context(focus_start)
            except Exception:
                pass

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

    official_solution = None
    if action:
        action_name = action.get("action")
        target_step_id = action.get("target_step_id")

        if action_name == "solve_step" and target_step_id in active_nodes:
            completed_steps.add(target_step_id)
            active_nodes = get_active_unlocked_nodes(steps_dict, completed_steps)
            current_focus = active_nodes[0] if active_nodes else None
            for step in active_nodes:
                if step not in completed_steps:
                    step_start_times[step] = now.isoformat()

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

    notebook_entries = []
    if dynamic_note:
        notebook_entries.append(dynamic_note.model_dump(mode="json"))
    if official_solution:
        notebook_entries.append(official_solution.model_dump(mode="json"))

    push_payload = {
        "chat_history": {
            "$each": [
                {"role": "user", "content": body.user_text},
                {"role": "assistant", "content": ai_response},
            ]
        }
    }
    if notebook_entries:
        push_payload["notebook_history"] = {"$each": notebook_entries}

    db_updates = {
        "$push": push_payload,
        "$set": {
            "completed_steps": list(completed_steps),
            "current_focused_step": current_focus,
            "step_start_times": step_start_times,
            "updated_at": now_iso,
        }
    }
    await db.sessions.update_one({"session_id": session_id}, db_updates)

    is_complete_now = len(completed_steps) >= len(step_keys)
    return ChatResponse(
        ai_response=ai_response,
        phase=phase,
        is_correct=False,
        verifier_signal=verifier_signal,
        is_complete=is_complete_now,
        notebook_updates=NotebookUpdates(
            dynamic_note=dynamic_note,
            official_solution=official_solution,
        ),
        new_active_nodes=active_nodes,
        focused_step=current_focus
    )
