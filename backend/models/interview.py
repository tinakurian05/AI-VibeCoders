from typing import Optional, Dict, Any, List
from pydantic import BaseModel, field_validator


# =====================================================================
# PART 2: Candidate Profile State (PRE-INTERVIEW FACTS ONLY)
# =====================================================================

class CandidateMember(BaseModel):
    """Schema for candidate member profile details."""
    id: str
    name: str
    jobRole: str
    yearsExperience: int
    education: str
    status: str


class CandidateMission(BaseModel):
    """Schema for an individual mission completed or attempted by a candidate."""
    day: int
    title: str
    passed: Optional[bool] = None
    attempts: Optional[int] = None
    skipped: Optional[bool] = None


class CandidateSignals(BaseModel):
    """Schema for candidate activity signals."""
    commitDays: int
    missionsCompleted: int
    missionsFirstTry: int


class CandidateState(BaseModel):
    """
    Parsed and normalized state representation of pre-interview candidate facts.
    
    IMPORTANT: CandidateState represents pre-interview background facts only.
    It does NOT represent live technical knowledge scores or understanding levels.
    """
    candidate_id: str
    name: str
    job_role: str
    years_experience: int
    education: str
    status: str
    completed_days: List[int] = []
    skipped_days: List[int] = []
    attempts: Dict[int, int] = {}
    mission_titles: Dict[int, str] = {}
    signals: CandidateSignals


# =====================================================================
# PART 3: Curriculum Context (Derived context for interview execution)
# =====================================================================

class CurriculumDay(BaseModel):
    """Schema for an individual curriculum day topic record."""
    day: int
    title: str
    type: str
    tools: List[str] = []
    objectives: List[str] = []


class CurriculumModule(BaseModel):
    """Schema for a curriculum module containing associated curriculum days."""
    module_id: int
    title: str
    day_range: List[int] = []
    days: List[CurriculumDay] = []


class CurriculumState(BaseModel):
    """Parsed and normalized state representation of the entire curriculum."""
    cohort: str
    modules: Dict[int, CurriculumModule] = {}
    days: Dict[int, CurriculumDay] = {}


class CurriculumContextDay(BaseModel):
    """Derived curriculum day representation tailored for interview context."""
    day: int
    title: str
    type: str
    tools: List[str] = []
    objectives: List[str] = []


class CurriculumContext(BaseModel):
    """Derived curriculum context derived from CurriculumState and InterviewPlan."""
    cohort: str
    target_days: List[CurriculumContextDay] = []
    module_titles: Dict[int, str] = {}


# =====================================================================
# Interview Plan Models
# =====================================================================

class InterviewTopicPlan(BaseModel):
    """Schema for a selected curriculum topic included in an interview plan."""
    day: int
    title: str
    module_id: int
    module_title: str
    question_count: int
    priority_score: float
    attempts: int
    follow_up_allowed: bool = True
    probing_reason: str
    tools: List[str] = []
    objectives: List[str] = []


class InterviewPlan(BaseModel):
    """Schema for a generated interview plan."""
    candidate_id: str
    candidate_name: str
    job_role: str
    selected_days: List[int]
    total_question_budget: int
    topic_plans: List[InterviewTopicPlan]
    min_questions_met: bool = True
    min_days_met: bool = True
    notes: Optional[str] = None


# =====================================================================
# PART 4: InterviewState (LIVE INTERVIEW PROGRESS)
# =====================================================================

class InterviewState(BaseModel):
    """
    Dedicated state representation tracking the LIVE interview execution.
    
    Separated strictly from pre-interview CandidateState.
    """
    session_id: str
    candidate_id: str
    current_turn: int = 0
    question_count: int = 0
    interview_plan: Optional[InterviewPlan] = None
    current_question: Optional[str] = None
    current_question_meta: Optional[Dict[str, Any]] = None
    conversation: List[Dict[str, str]] = []
    covered_days: List[int] = []
    completed_question_ids: List[str] = []
    current_topic_day: Optional[int] = None
    done: bool = False
    interview_started: bool = False
    interview_completed: bool = False


# =====================================================================
# PART 5: CandidateKnowledgeModel (DERIVED TECHNICAL UNDERSTANDING)
# =====================================================================

class ObjectiveKnowledge(BaseModel):
    """Technical understanding belief state for a specific learning objective."""
    objective_id: str
    text: str
    understanding_level: str = "UNKNOWN"  # e.g., "UNKNOWN", "HIGH", "MEDIUM", "LOW"
    confidence: Optional[float] = None
    evidence_ids: List[str] = []


class CandidateTopicKnowledge(BaseModel):
    """Technical understanding belief state for a specific topic (curriculum day)."""
    curriculum_day: int
    topic: str
    understanding_level: str = "UNKNOWN"  # e.g., "UNKNOWN", "HIGH", "MEDIUM", "LOW"
    confidence: Optional[float] = None     # null / None at init
    depth_confidence: Optional[float] = None
    reasoning_confidence: Optional[float] = None
    communication_confidence: Optional[float] = None
    strengths: List[str] = []
    gaps: List[str] = []
    evidence_ids: List[str] = []
    objectives: Dict[str, ObjectiveKnowledge] = {}


class CandidateKnowledgeModel(BaseModel):
    """
    Represents what the interviewer currently believes about the candidate's
    technical understanding based strictly on live interview evidence.
    
    Initializes empty/unknown. Must NOT be pre-populated from CandidateState.
    """
    candidate_id: str
    topics: Dict[int, CandidateTopicKnowledge] = {}
    misconceptions: List[str] = []
    global_signals: Dict[str, Optional[float]] = {
        "communication": None,
        "reasoning": None,
        "confidence": None,
    }


# =====================================================================
# PART 6: EvidenceLedger (SUPPORTING EVIDENCE FOR KNOWLEDGE MODEL)
# =====================================================================

class EvidenceItem(BaseModel):
    """An individual piece of interview evidence extracted from candidate responses."""
    evidence_id: str
    session_id: str
    question_id: str
    candidate_id: str
    curriculum_day: int
    topic: str
    objective_id: Optional[str] = None
    candidate_claim: str
    evidence_text: str
    assessment: str  # e.g. "supports_understanding", "indicates_gap", "ambiguous", "needs_follow_up"
    confidence: Optional[float] = None
    turn: int = 0


class EvidenceLedger(BaseModel):
    """Structured ledger storing all evidence supporting CandidateKnowledgeModel updates."""
    session_id: str
    items: List[EvidenceItem] = []

    def add_evidence(self, item: EvidenceItem) -> None:
        self.items.append(item)

    def get_evidence_for_day(self, curriculum_day: int) -> List[EvidenceItem]:
        return [item for item in self.items if item.curriculum_day == curriculum_day]


# =====================================================================
# PART 7: LLM Boundary & Response Schemas
# =====================================================================

class LLMResponse(BaseModel):
    """
    Normalized internal representation of an LLM generation response.
    Provider-agnostic structure returned by LLMGateway.
    """
    content: str
    model_used: str
    provider: str = "groq"
    latency_ms: float = 0.0
    success: bool = True
    error_category: Optional[str] = None


class CandidateEvidenceAnalysis(BaseModel):
    """
    Structured output returned by future LLM AnswerAnalyzer.
    
    IMPORTANT: The LLM returns this data structure. The LLM does NOT directly
    mutate application state. The backend validates and applies this analysis.
    """
    curriculum_day: int
    topic: str
    understanding_assessment: str  # e.g. "HIGH", "MEDIUM", "LOW"
    assessment_type: str            # e.g. "supports_understanding", "indicates_gap"
    confidence: float
    strengths: List[str] = []
    gaps: List[str] = []
    evidence_text: str
    candidate_claim: str
    follow_up_recommended: bool = False


# =====================================================================
# API Request / Response Schemas
# =====================================================================

class InterviewRequest(BaseModel):
    """
    Schema for incoming interview request payload.
    Supports either initializing an interview with a candidateId/candidate object
    or submitting a candidate response message during an ongoing session.
    """
    sessionId: str
    candidateId: Optional[str] = None
    candidate: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

    @field_validator("sessionId")
    @classmethod
    def session_id_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("sessionId must not be empty")
        return v.strip()


class Feedback(BaseModel):
    """Schema for post-interview feedback summary."""
    summary: str
    strengths: List[str] = []
    gaps: List[str] = []
    next: List[str] = []


class InterviewResponse(BaseModel):
    """Schema for interview endpoint response payload."""
    reply: str
    done: bool = False
    feedback: Optional[Feedback] = None
