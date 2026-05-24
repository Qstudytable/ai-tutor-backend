from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

import sympy as sp
from sympy.parsing.latex import parse_latex


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
    def get_phase_context(step_start_time: datetime) -> tuple[PedagogyPhase, str]:
        if step_start_time.tzinfo is None:
            step_start_time = step_start_time.replace(tzinfo=timezone.utc)

        elapsed_seconds = (datetime.now(timezone.utc) - step_start_time).total_seconds()

        if elapsed_seconds < 180:
            return (
                PedagogyPhase.SOCRATIC,
                "Ask guiding questions. Maximum of two lines is allowed. Do not give formulas, substitutions, final values, or the answer.",
            )
        if elapsed_seconds < 240:
            return (
                PedagogyPhase.DIRECT,
                "Give the specific formula and explain how to substitute values, but do not reveal the final value.Explain the step in detail and oonly the step detail in one message.",
            )
        return (
            PedagogyPhase.REVEAL,
            "Provide the final calculation, final value, and a concise explanation.",
        )

    @staticmethod
    def verify_math(user_input: str, truth_latex: str) -> tuple[bool, VerifierSignal]:
        if not user_input or not user_input.strip():
            return False, VerifierSignal.EMPTY_INPUT

        try:
            truth_expr = ChronosEngine._parse_truth_expression(truth_latex)
        except Exception:
            return False, VerifierSignal.SERVER_TRUTH_ERROR

        try:
            normalized_user = user_input.replace("^", "**").strip()
            user_expr = sp.sympify(normalized_user)

            if sp.simplify(user_expr - truth_expr) == 0:
                return True, VerifierSignal.CORRECT

            if sp.simplify(user_expr + truth_expr) == 0:
                return False, VerifierSignal.SIGN_FLIP

            return False, VerifierSignal.INCORRECT
        except Exception:
            return False, VerifierSignal.PARSING_ERROR

    @staticmethod
    def _parse_truth_expression(truth_latex: str) -> sp.Expr:
        normalized_truth = truth_latex.replace("^", "**").strip()

        try:
            return sp.sympify(normalized_truth)
        except Exception:
            return parse_latex(truth_latex)
