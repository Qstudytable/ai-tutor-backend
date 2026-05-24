from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from engine import PedagogyPhase, VerifierSignal

class ChatRequest(BaseModel):
    user_text: str

class NotebookOfficialSolution(BaseModel):
    step_key: str
    theorem: str
    formula: str
    result: Optional[str] = None
    timestamp: datetime | str

class NotebookDynamicNote(BaseModel):
    concept: str
    formula: Optional[str] = None
    insight: str
    timestamp: datetime | str

class NotebookUpdates(BaseModel):
    official_solution: Optional[NotebookOfficialSolution] = None
    dynamic_note: Optional[NotebookDynamicNote] = None

class ChatResponse(BaseModel):
    ai_response: str
    phase: PedagogyPhase
    is_correct: bool
    verifier_signal: VerifierSignal
    is_complete: bool
    notebook_updates: NotebookUpdates
    new_active_nodes: List[str] = Field(default_factory=list)
    focused_step: Optional[str] = None

class StartSessionResponse(BaseModel):
    session_id: str
    question_id: str
    context: str
    sub_questions: List[str]

class SessionSnapshotResponse(BaseModel):
    session_id: str
    question_id: str
    completed_steps: List[str] = Field(default_factory=list)
    focused_step: Optional[str] = None
    is_complete: bool
    notebook_history: List[Dict[str, Any]] = Field(default_factory=list)
    chat_history: List[Dict[str, Any]] = Field(default_factory=list)
    tutoring_mode: str = "socratic"
    steps_metadata: Dict[str, Any] = Field(default_factory=dict)
    difficulty: str = "medium"
    theorems: List[str] = Field(default_factory=list)
