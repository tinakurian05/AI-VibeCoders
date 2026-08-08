from typing import List, Dict, Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from models.strategy import StrategyDecision, DifficultyLevel
from models.interview import (
    InterviewState,
    InterviewPlan,
    CandidateKnowledgeModel,
    EvidenceLedger,
    CandidateEvidenceAnalysis,
    EvidenceItem,
)

class QuestionGeneratorError(Exception):
    """Error raised by QuestionGenerator when generation fails or is not allowed."""
    pass

class InterviewShouldEnd(Exception):
    """Raised when the strategy indicates the interview should end; no question is generated."""
    pass

class QuestionGeneratorInput(BaseModel):
    """Input required for generating the next interview question.

    Includes minimal context needed to produce a focused question.
    """
    candidate_id: str
    strategy_decision: StrategyDecision
    interview_state: InterviewState
    interview_plan: InterviewPlan
    # Optional fields for candidate data; default to None if not provided in tests
    knowledge_model: Optional[CandidateKnowledgeModel] = None
    evidence_ledger: Optional[EvidenceLedger] = None
    latest_analysis: Optional[CandidateEvidenceAnalysis] = None
    # Recent evidence and conversation for context (optional, default empty list)
    recent_evidence: List[EvidenceItem] = []
    recent_conversation: List[Dict[str, str]] = []
    relevant_memories: List[Dict[str, Any]] = []

class GeneratedQuestion(BaseModel):
    """Structured output produced by the Question Generator.

    ``question_id`` is a UUID string unique to the current session.
    """
    question_id: str = Field(default_factory=lambda: str(uuid4()))
    question: str
    target_day: int
    target_objective: Optional[str] = None
    difficulty: DifficultyLevel
    intent: str

    class Config:
        extra = "forbid"
