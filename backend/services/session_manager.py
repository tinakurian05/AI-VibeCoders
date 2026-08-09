import uuid
from typing import Dict, Any, Optional, List
from models.interview import (
    CandidateState,
    InterviewState,
    InterviewPlan,
    CandidateKnowledgeModel,
    CandidateTopicKnowledge,
    ObjectiveKnowledge,
    EvidenceLedger,
    EvidenceItem,
    CandidateEvidenceAnalysis,
)
from services.candidate_profile_service import candidate_profile_service
from services.curriculum_service import curriculum_service
from services.interview_planner import interview_planner


class SessionManager:
    """
    In-memory session manager orchestrating the 4 distinct state layers:
    
    1. CandidateState: Immutable pre-interview facts from candidates.json.
    2. InterviewState: Live interview progress (turn count, questions, plan, status).
    3. CandidateKnowledgeModel: Derived technical belief state updated ONLY via evidence analysis.
    4. EvidenceLedger: Linked log of evidence items supporting technical belief state.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def clear_all(self) -> None:
        """Clear all active sessions (useful for test isolation)."""
        self._sessions.clear()

    def create_session(self, session_id: str, candidate: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initialize a new session maintaining clear 4-layer state isolation."""
        # Ensure curriculum state is available via load_curriculum()
        curriculum_state = curriculum_service.load_curriculum()
        
        # Layer 1: CandidateState (pre-interview facts ONLY)
        candidate_state: Optional[CandidateState] = None
        candidate_id = "UNKNOWN"
        interview_plan: Optional[InterviewPlan] = None
        if candidate is not None:
            try:
                candidate_state = candidate_profile_service.build_candidate_state(candidate)
                candidate_id = candidate_state.candidate_id
                interview_plan = interview_planner.plan_interview(candidate_state, curriculum_state)
            except Exception:
                candidate_state = None

        # Layer 2: InterviewState (live execution progress)
        interview_state = InterviewState(
            session_id=session_id,
            candidate_id=candidate_id,
            current_turn=0,
            question_count=0,
            interview_plan=interview_plan,
            conversation=[],
            covered_days=[],
            done=False,
            interview_started=True,
            interview_completed=False,
        )

        # Layer 3: CandidateKnowledgeModel
        topics = {}
        for day_num, day_obj in curriculum_state.days.items():
            objectives_map = {}
            for idx, obj_text in enumerate(day_obj.objectives):
                obj_id = f"day-{day_num}-obj-{idx}"
                objectives_map[obj_id] = ObjectiveKnowledge(
                    objective_id=obj_id,
                    text=obj_text,
                    understanding_level="UNKNOWN",
                    confidence=None,
                    evidence_ids=[]
                )
            
            topics[day_num] = CandidateTopicKnowledge(
                curriculum_day=day_num,
                topic=day_obj.title,
                understanding_level="UNKNOWN",
                confidence=None,
                depth_confidence=None,
                reasoning_confidence=None,
                communication_confidence=None,
                strengths=[],
                gaps=[],
                evidence_ids=[],
                objectives=objectives_map
            )

        knowledge_model = CandidateKnowledgeModel(
            candidate_id=candidate_id,
            topics=topics,
            misconceptions=[],
            global_signals={
                "communication": None,
                "reasoning": None,
                "confidence": None,
            }
        )

        # Layer 4: EvidenceLedger
        evidence_ledger = EvidenceLedger(
            session_id=session_id,
            items=[]
        )

        session_data: Dict[str, Any] = {
            "session_id": session_id,
            "candidate": candidate,
            "candidate_state": candidate_state,
            "curriculum_state": curriculum_state,
            "interview_state": interview_state,
            "knowledge_model": knowledge_model,
            "evidence_ledger": evidence_ledger,
            "question_count": 0,
            "conversation": [],
            "conversation_history": [],
            "done": False,
        }
        self._sessions[session_id] = session_data
        return session_data

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an existing session by session_id, or None if not found."""
        return self._sessions.get(session_id)

    def session_exists(self, session_id: str) -> bool:
        """Check if a session with the given session_id exists."""
        return session_id in self._sessions

    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """Append a conversation message to an existing session's history."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        message_dict = {"role": role, "content": content}
        session["conversation"].append(message_dict)
        if "conversation_history" in session:
            session["conversation_history"].append(message_dict)
        
        if session.get("interview_state"):
            session["interview_state"].conversation.append(message_dict)
            session["interview_state"].current_turn += 1
            
        return True

    def apply_evidence_analysis(
        self,
        session_id: str,
        analysis: CandidateEvidenceAnalysis,
        question_id: str = "",
        objective_id: Optional[str] = None
    ) -> Optional[EvidenceItem]:
        """
        Validate and apply a CandidateEvidenceAnalysis object to session state.
        
        - Creates an EvidenceItem and appends it to EvidenceLedger.
        - Updates CandidateKnowledgeModel topic/objective scores based on evidence.
        """
        session = self.get_session(session_id)
        if not session:
            return None

        ledger: EvidenceLedger = session["evidence_ledger"]
        knowledge: CandidateKnowledgeModel = session["knowledge_model"]
        interview_state: InterviewState = session["interview_state"]

        turn = interview_state.question_count + 1
        ev_id = f"ev-{uuid.uuid4().hex[:8]}"
        cand_id = session["candidate_state"].candidate_id if session.get("candidate_state") else interview_state.candidate_id

        ev_item = EvidenceItem(
            evidence_id=ev_id,
            session_id=session_id,
            question_id=question_id or f"q-{turn}",
            candidate_id=cand_id,
            curriculum_day=analysis.curriculum_day,
            topic=analysis.topic,
            objective_id=objective_id,
            candidate_claim=analysis.candidate_claim,
            evidence_text=analysis.evidence_text,
            assessment=analysis.assessment_type or analysis.understanding_assessment,
            confidence=analysis.confidence,
            turn=turn,
        )
        
        ledger.items.append(ev_item)

        day = analysis.curriculum_day
        if day in knowledge.topics:
            topic_k = knowledge.topics[day]
            topic_k.understanding_level = analysis.understanding_assessment
            topic_k.confidence = analysis.confidence
            
            for s in analysis.strengths:
                if s not in topic_k.strengths:
                    topic_k.strengths.append(s)
            for g in analysis.gaps:
                if g not in topic_k.gaps:
                    topic_k.gaps.append(g)

            if ev_id not in topic_k.evidence_ids:
                topic_k.evidence_ids.append(ev_id)

            if objective_id and objective_id in topic_k.objectives:
                obj_k = topic_k.objectives[objective_id]
                obj_k.understanding_level = analysis.understanding_assessment
                obj_k.confidence = analysis.confidence
                if ev_id not in obj_k.evidence_ids:
                    obj_k.evidence_ids.append(ev_id)

        return ev_item


session_manager = SessionManager()
