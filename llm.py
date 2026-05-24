from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from engine import PedagogyPhase, VerifierSignal
from schemas import NotebookDynamicNote


NOTEBOOK_TOOL = {
    "type": "function",
    "function": {
        "name": "append_to_notebook",
        "description": "Capture a useful student realization, misconception correction, or durable formula note.",
        "parameters": {
            "type": "object",
            "properties": {
                "concept": {"type": "string"},
                "formula": {"type": "string"},
                "insight": {"type": "string"},
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
    budget: dict[str, Any] = {
        "theorem": theorem,
        "socratic_hint": hint,
        "revealed_notebook_history": notebook_history,
    }

    if phase in {PedagogyPhase.DIRECT, PedagogyPhase.REVEAL}:
        budget["formula_guidance"] = formula

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
    system_prompt = f"""
ROLE: Elite 1-on-1 tutor.

PEDAGOGICAL PHASE: {phase}
PHASE INSTRUCTION: {phase_instruction}
VERIFIER SIGNAL: {verifier_signal}
TUTORING MODE: {tutoring_mode}

KNOWLEDGE BUDGET:
{json.dumps(knowledge_budget, default=str)}

RULES:
- Never use information that is absent from the knowledge budget.
- In SOCRATIC, ask one focused guiding question and do not provide formulas, substitutions, or final values. Use maximum of two sentences.
- In DIRECT, explain the relevant formula and substitution path, but do not provide the final value.
- In REVEAL, explain the final calculation clearly and briefly.
- If the verifier signal is CORRECT, celebrate briefly and explain why the step works.
- If the verifier signal is SIGN_FLIP, guide the student to inspect the sign convention.
- Use append_to_notebook only for durable insights worth saving.
""".strip()

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend({"role": msg["role"], "content": msg["content"]} for msg in recent_history[-4:])
    messages.append({"role": "user", "content": user_text})
    return messages


def _extract_text_and_note_and_action(response: Any) -> tuple[str, NotebookDynamicNote | None, dict[str, Any] | None]:
    message = response.choices[0].message
    text = message.content or ""
    dynamic_note = None
    action = None

    for call in getattr(message, "tool_calls", None) or []:
        function = getattr(call, "function", None)
        if not function:
            continue
            
        if function.name == "append_to_notebook":
            try:
                args = json.loads(function.arguments or "{}")
                dynamic_note = NotebookDynamicNote(
                    concept=args.get("concept", ""),
                    formula=args.get("formula"),
                    insight=args.get("insight", ""),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            except (json.JSONDecodeError, ValidationError):
                dynamic_note = None

    if not text and dynamic_note:
        text = f"I saved that insight about {dynamic_note.concept}."

    return text, dynamic_note, action


async def complete_tutor_turn(messages: list[dict[str, str]]) -> tuple[str, NotebookDynamicNote | None, dict[str, Any] | None]:
    from litellm import completion

    model = os.getenv("LLM_MODEL", "gemini/gemini-1.5-flash")
    try:
        response = await asyncio.to_thread(
            completion,
            model=model,
            messages=messages,
            tools=[NOTEBOOK_TOOL],
            tool_choice="auto",
        )
        return _extract_text_and_note_and_action(response)
    except Exception as e:
        # Failsafe so the API never crashes if the LLM provider blips
        return "I'm having a little trouble connecting to my logic engine. Can you explain your thought process?", None, None

# ---> ADDED BACK THE MISSING FUNCTION <---
async def generate_transition_message(solved_theorem: str, next_theorem: str | None) -> str:
    from litellm import completion
    if next_theorem:
        prompt = f"The student just solved '{solved_theorem}'. Celebrate briefly (1 sentence), then introduce the next step: '{next_theorem}'. Ask a guiding question to start."
    else:
        prompt = f"The student just solved '{solved_theorem}' and finished the whole problem! Celebrate their success enthusiastically."
        
    model = os.getenv("LLM_MODEL", "gemini/gemini-1.5-flash")
    try:
        response = await asyncio.to_thread(
            completion,
            model=model,
            messages=[{"role": "system", "content": prompt}]
        )
        return response.choices[0].message.content or "Great job! Let's move on."
    except Exception:
        return "Excellent work! Let's tackle the next part."
