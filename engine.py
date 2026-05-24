import re
from enum import Enum
import sympy

class PedagogyPhase(Enum):
    SOCRATIC = "SOCRATIC"
    DIRECT = "DIRECT"
    REVEAL = "REVEAL"

class ChronosEngine:
    @staticmethod
    def get_phase_context(attempts: int) -> tuple[PedagogyPhase, str]:
        if attempts < 3:
            return (PedagogyPhase.SOCRATIC, "Ask ONE short guiding question. NEVER give formulas or values.")
        elif attempts < 5:
            return (PedagogyPhase.DIRECT, "Give the specific formula. Explain exactly how to substitute values.")
        else:
            return (PedagogyPhase.REVEAL, "The student is deeply stuck. Provide the final calculation clearly.")

    @staticmethod
    def extract_math_from_text(text: str) -> str:
        cleaned = re.sub(r'(?i)(i think|maybe|is it|the answer is|so|would it be|equals)', '', text)
        return cleaned.strip()

    @staticmethod
    def verify_math(user_input: str, expected_formula: str) -> tuple[bool, str]:
        # Basic SymPy verification stub for your demo
        try:
            # In a real scenario, you'd parse both with sympy.parse_expr
            return (user_input.replace(" ", "") == expected_formula.replace(" ", "")), "Verified"
        except Exception:
            return False, "Error parsing math"