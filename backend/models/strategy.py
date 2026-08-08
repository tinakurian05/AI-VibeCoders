from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from models.interview import (
    InterviewState,
    InterviewPlan,
    CandidateKnowledgeModel,
    EvidenceLedger,
    CandidateEvidenceAnalysis,
)

class StrategyAction(str, Enum):
    FOLLOW_UP = "FOLLOW_UP"
    DEEPEN = "DEEPEN"
    MOVE_TOPIC = "MOVE_TOPIC"
    CHANGE_DIFFICULTY = "CHANGE_DIFFICULTY"
    CLARIFY = "CLARIFY"
    END = "END"

class DifficultyLevel(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"

class StrategyDecision(BaseModel):
    action: StrategyAction
    target_day: int
    target_objective: Optional[str] = None
    difficulty: DifficultyLevel
    intent: str
    reasoning: str
    follow_up: bool
    should_end: bool

class StrategyEngineInput(BaseModel):
    interview_state: InterviewState
    interview_plan: InterviewPlan
    knowledge_model: CandidateKnowledgeModel
    evidence_ledger: EvidenceLedger
    latest_analysis: CandidateEvidenceAnalysis
    relevant_memories: List[Dict[str, Any]] = []
