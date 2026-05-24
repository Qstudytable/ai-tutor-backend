import os
import asyncio
from litellm import completion

# 1. The missing function that main.py needs!
async def generate_transition_message(solved_theorem: str, next_theorem: str | None) -> str:
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

# 2. Your advanced tutor logic, safely adapted so it doesn't crash looking for schemas.py
async def complete_tutor_turn(user_text: str, phase_instruction: str) -> str:
    system_prompt = f"""
ROLE: Elite 1-on-1 tutor.
PHASE INSTRUCTION: {phase_instruction}

RULES:
- In SOCRATIC, ask one focused guiding question and do not provide formulas, substitutions, or final values. Use maximum of two sentences.
- In DIRECT, explain the relevant formula and substitution path, but do not provide the final value.
- In REVEAL, explain the final calculation clearly and briefly.
""".strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text}
    ]

    model = os.getenv("LLM_MODEL", "gemini/gemini-1.5-flash")
    try:
        response = await asyncio.to_thread(
            completion,
            model=model,
            messages=messages
        )
        return response.choices[0].message.content or "Can you explain your thought process?"
    except Exception:
        return "I'm here to help. What part are you stuck on?"
