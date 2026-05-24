from __future__ import annotations

import logging
import re
from enum import StrEnum
import sympy as sp
from sympy.parsing.latex import parse_latex

# Setup localized logger for safety debugging
logger = logging.getLogger("ai_tutoring_engine.engine")


class PedagogyPhase(StrEnum):
    SOCRATIC = "SOCRATIC"
    DIRECT = "DIRECT"
    REVEAL = "REVEAL"


class VerifierSignal(StrEnum):
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    SIGN_FLIP = "SIGN_FLIP"
    PARSING_ERROR = "PARSING_ERROR"
    EMPTY_INPUT = "EMPTY_INPUT"
    SERVER_TRUTH_ERROR = "SERVER_TRUTH_ERROR"


class ChronosEngine:
    @staticmethod
    def get_phase_context(attempts: int) -> tuple[PedagogyPhase, str]:
        """
        Determines pedagogy strictly based on integer failure counts (V3).
        Eliminates network lag and idle-time bugs.
        """
        if attempts < 3:
            return (
                PedagogyPhase.SOCRATIC,
                "Ask ONE short guiding question. NEVER give formulas, values, or calculations. Max 2 sentences.",
            )
        elif attempts < 5:
            return (
                PedagogyPhase.DIRECT,
                "Give the specific formula. Explain exactly how to substitute values, but do not provide the final calculated answer.",
            )
        else:
            return (
                PedagogyPhase.REVEAL,
                "The student is deeply stuck. Provide the final calculation and the final value clearly and concisely.",
            )

    @staticmethod
    def extract_math_from_text(text: str) -> str:
        """
        Surgically strips conversational wrapper phrases to isolate math equations.
        Prevents SymPy from trying to parse English words as variables.
        """
        if not text:
            return ""
        
        # Strip common student conversational conversational structures
        cleaned = re.sub(
            r'(?i)\b(i think|maybe|is it|the answer is|so|would it be|equals|it should be|perhaps)\b', 
            '', 
            text
        )
        # Strip trailing/leading punctuation conversational remnants
        cleaned = re.sub(r'^[?,.\s]+|[?,.\s]+$', '', cleaned)
        return cleaned.strip()

    @staticmethod
    def verify_math(user_input: str, truth_latex: str) -> tuple[bool, VerifierSignal]:
        """
        A highly resilient multi-pass verification engine.
        Pass 1: Direct symbolic math check (SymPy).
        Pass 2: LaTeX parser mathematical equality fallback.
        """
        if not user_input or not user_input.strip():
            return False, VerifierSignal.EMPTY_INPUT

        user_clean = ChronosEngine.extract_math_from_text(user_input)
        if not user_clean:
            return False, VerifierSignal.EMPTY_INPUT

        # Step A: Safe parsing of the system's ground truth
        try:
            truth_expr = ChronosEngine._parse_truth_expression(truth_latex)
        except Exception as e:
            logger.error(f"Failsafe triggered: Truth latex '{truth_latex}' could not be parsed: {e}")
            return False, VerifierSignal.SERVER_TRUTH_ERROR

        # Step B: Pass 1 - Try Standard Symbolic Sympy Normalization
        try:
            normalized_user = user_clean.replace("^", "**").strip()
            user_expr = sp.sympify(normalized_user)

            if sp.simplify(user_expr - truth_expr) == 0:
                return True, VerifierSignal.CORRECT

            if sp.simplify(user_expr + truth_expr) == 0:
                return False, VerifierSignal.SIGN_FLIP

            return False, VerifierSignal.INCORRECT

        except Exception:
            # Step C: Pass 2 - LaTeX parsing fallback if student entered raw LaTeX (e.g. fractions, divisions)
            try:
                user_expr = parse_latex(user_clean)
                
                if sp.simplify(user_expr - truth_expr) == 0:
                    return True, VerifierSignal.CORRECT
                
                if sp.simplify(user_expr + truth_expr) == 0:
                    return False, VerifierSignal.SIGN_FLIP
                
                return False, VerifierSignal.INCORRECT
            except Exception as e:
                logger.warning(f"Could not parse user input '{user_clean}' through math engine: {e}")
                return False, VerifierSignal.PARSING_ERROR

    @staticmethod
    def _parse_truth_expression(truth_latex: str) -> sp.Expr:
        """Helper to ensure truth expressions parse under Sympy or LaTeX engine rules."""
        normalized_truth = truth_latex.replace("^", "**").strip()
        try:
            return sp.sympify(normalized_truth)
        except Exception:
            return parse_latex(truth_latex)
