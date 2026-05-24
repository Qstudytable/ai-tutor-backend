from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("ai_tutoring_engine.middleware")


def preprocess_question_graph(steps: dict[str, Any]) -> dict[str, Any]:
    """
    Ensure steps have depends_on lists. 
    Only infers linear dependencies if the 'depends_on' key is entirely absent.
    If 'depends_on' is present but is [], it is preserved (representing start nodes).
    """
    step_keys = list(steps.keys())
    for i, key in enumerate(step_keys):
        if 'depends_on' not in steps[key]:
            # If the key is completely missing, infer linear fallback
            steps[key]['depends_on'] = [step_keys[i-1]] if i > 0 else []
    return steps


def get_active_unlocked_nodes(all_steps: dict[str, Any], completed_steps: set[str]) -> list[str]:
    """
    Determine which step nodes are unlocked based on completed steps.
    """
    active_nodes = []
    for step_id, step_data in all_steps.items():
        if step_id in completed_steps:
            continue
        deps = step_data.get('depends_on', [])
        if not isinstance(deps, list):
            deps = [deps] if deps else []
        deps_set = set(deps)
        if deps_set.issubset(completed_steps):
            active_nodes.append(step_id)
    return active_nodes
