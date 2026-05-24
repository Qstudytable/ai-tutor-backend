from __future__ import annotations

import asyncio
import json
import os
import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from engine import PedagogyPhase, VerifierSignal
from schemas import NotebookDynamicNote

logger = logging.getLogger("ai_tutoring_engine.llm")

# Schema for the LLM to call when capturing durable student insights
NOTEBOOK_TOOL = {
    "type": "function",
    "function": {
        "name": "append_to_notebook",
        "description": "Capture a durable physics concept realization, theorem, or student misconception correction.",
        "parameters": {
            "type": "object",
            "properties": {
                "concept": {"type": "string", "description": "The physics formula or principle being learned (e.g. Faraday's Law)"},
                "formula": {"type": "string", "description": "The mathematical formula if applicable (e.g. E = N*B*A*w)"},
                "insight": {"type": "string", "description": "A 1-sentence summary of what the student successfully realized or resolved."},
            },
            "required": ["concept", "insight"],
        },
    },
}


def build_knowledge_budget(
    *,
    phase: PedagogyPhase,
    theorem: str,
    hint: str,
    formula: str,
    final_value: str | None,
    notebook_history: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Limits the information the LLM has access to based on the pedagogical phase.
    This prevents the model from leaking final answers too early.
    """
    budget: dict[str, Any] = {
        "theorem": theorem,
        "socratic_hint": hint,
        "unlocked_notebook_history": notebook_history,
    }

    # Only let the LLM see the math formula when the student has reached DIRECT or REVEAL mode
    if phase in {PedagogyPhase.DIRECT, PedagogyPhase.REVEAL}:
        budget["formula_guidance"] = formula

    # Only let the LLM see the final calculated solution during the REVEAL phase
    if phase == PedagogyPhase.REVEAL:
        budget["final_truth"] = formula
        budget["final_value"] = final_value

    return budget


def build_tutor_messages(
    *,
    phase: PedagogyPhase,
    phase_instruction: str,
    verifier_signal: VerifierSignal,
    knowledge_budget: dict[str, Any],
    recent_history: list[dict[str, str]],
    user_text: str,
    tutoring_mode: str = "socratic",
    active_nodes: list[str] = None,
    focused_step: str = None
) -> list[dict[str, str]]:
    """
    Assembles the strict system instruction set and historical context array for the LLM.
    """
    system_prompt = f"""
ROLE: You are an elite, highly encouraging 1-on-1 High School Physics Tutor.

CURRENT PEDAGOGICAL PHASE: {phase}
PHASE INSTRUCTIONS: {phase_instruction}
CURRENT STUDENT SIGNAL: {verifier_signal}
TUTORING MODE: {tutoring_mode}

AUTHORIZED KNOWLEDGE BUDGET:
{json.dumps(knowledge_budget, default=str)}

STRICT OPERATIONAL DIRECTIVES:
1. Never refer to variables, values, or formulas that are absent from the AUTHORIZED KNOWLEDGE BUDGET.
2. In SOCRATIC phase: Ask ONE short, precise guiding question. Never give the formulas, math steps, or answers. Be warm but disciplined. Max 2 sentences.
3. In DIRECT phase: Explain the formula in your budget and describe how to substitute known variables. Do NOT compute or reveal the final numerical value.
4. In REVEAL phase: Explain the math pipeline, substitute the variables, and display the final calculation value clearly.
5. If STUDENT SIGNAL is CORRECT: Do not re-evaluate their math. Celebrate their correct answer warmly and introduce why the physical concept behaves this way.
6. If STUDENT SIGNAL is SIGN_FLIP: Gently nudge them to look closely at their coordinate system directions or mathematical signs.
7. Use the 'append_to_notebook' tool ONLY when the user makes a significant conceptual breakthrough, self-corrects a major misconception, or lands on a durable mathematical formula. Do not use it for mundane dialog.
""".strip()

    messages = [{"role": "system", "content": system_prompt}]
    
    # Restrict sliding window history to the last 4 exchanges to prevent prompt bloat and context drift
    for msg in recent_history[-4:]:
        role = "user" if msg["role"] == "user" or msg["role"] == "You" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
        
    messages.append({"role": "user", "content": user_text})
    return messages


def _extract_text_and_note_and_action(response: Any) -> tuple[str, NotebookDynamicNote | None, dict[str, Any] | None]:
    """
    Surgically parses the raw completion message payload to split text response and function tool calls.
    """
    message = response.choices[0].message
    text = message.content or ""
    dynamic_note = None
    action = None

    tool_calls = getattr(message, "tool_calls", None) or []
    for call in tool_calls:
        function = getattr(call, "function", None)
        if not function:
            continue
            
        if function.name == "append_to_notebook":
            try:
                args_str = function.arguments or "{}"
                args = json.loads(args_str)
                
                # Safeguard against malformed JSON structure
                dynamic_note = NotebookDynamicNote(
                    concept=args.get("concept", "Physics Insight"),
                    formula=args.get("formula"),
                    insight=args.get("insight", "Resolved problem step."),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            except Exception as e:
                logger.warning(f"Failed to parse function call arguments safely: {e}")
                dynamic_note = None

    if not text and dynamic_note:
        text = f"Great realization! I've noted down your insight on '{dynamic_note.concept}' in your study notebook."

    return text, dynamic_note, action


async def complete_tutor_turn(messages: list[dict[str, str]]) -> tuple[str, NotebookDynamicNote | None, dict[str, Any] | None]:
    """
    Fires the asynchronous turn request to the primary tutor LLM.
    Guarantees a safe fallback text response if the API call encounters latency spikes or network faults.
    """
    from litellm import completion

    model = os.getenv("LLM_MODEL", "gemini/gemini-2.5-flash")
    try:
        response = await asyncio.to_thread(
            completion,
            model=model,
            messages=messages,
            tools=[NOTEBOOK_TOOL],
            tool_choice="auto",
            timeout=8.0  # Safe boundary to avoid long-hanging connections
        )
        return _extract_text_and_note_and_action(response)
    except Exception as e:
        logger.error(f"Tutor LLM call exception triggered: {e}")
        return "I'm having a brief connection issue with my tutoring core. Could you restate your last thought so I can catch up?", None, None


async def generate_transition_message(solved_theorem: str, next_theorem: str | None) -> str:
    """
    Fast transition model call that bypasses the core Socratic logic.
    Fires immediately when a mathematical step is deterministically verified to celebrate and segue.
    """
    from litellm import completion
    
    if next_theorem:
        prompt = (
            f"The student just successfully solved the step for '{solved_theorem}'. "
            f"Celebrate their progress in exactly 1 brief sentence, then introduce the next step: "
            f"'{next_theorem}'. Ask a simple guiding question to prompt them to begin."
        )
    else:
        prompt = (
            f"The student just solved the step for '{solved_theorem}' and completed the entire physics problem! "
            f"Celebrate their final victory enthusiastically in 1-2 warm sentences."
        )
        
    model = os.getenv("LLM_MODEL", "gemini/gemini-2.5-flash")
    try:
        response = await asyncio.to_thread(
            completion,
            model=model,
            messages=[{"role": "system", "content": prompt}],
            timeout=5.0
        )
        return response.choices[0].message.content or "Excellent job! Let's carry this momentum forward."
    except Exception as e:
        logger.warning(f"Transition generator failed: {e}. Falling back to default canned text.")
        if next_theorem:
            return f"Perfect! You've unlocked '{solved_theorem}'. Let's tackle our next step: '{next_theorem}'."
        return "Outstanding work! You have fully resolved every step of this physics challenge."
