from typing import Optional, Dict, Any, List
import uuid
from models.interview import (
    CandidateState,
    InterviewState,
    CandidateKnowledgeModel,
    CandidateTopicKnowledge,
    EvidenceLedger,
    EvidenceItem,
    CandidateEvidenceAnalysis,
)
from services.candidate_profile_service import candidate_profile_service


class SessionManager:
    """
    Service responsible for managing interview sessions in memory across four core layers:
    1. CandidateState: Pre-interview candidate facts (profile, completed/skipped missions, signals).
    2. InterviewState: Live interview progress (turn count, questions, plan, status).
    3. CandidateKnowledgeModel: Derived technical understanding based on live evidence (initializes UNKNOWN).
    4. EvidenceLedger: Store of verified evidence items supporting knowledge model updates.
    """

    def __init__(self) -> None:
        # In-memory dictionary mapping session_id -> session data dict
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, session_id: str, candidate: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Initialize and store a new session managing all 4 architectural state layers.
        """
        # Layer 1: CandidateState (pre-interview facts)
        candidate_state: Optional[CandidateState] = None
        candidate_id = "UNKNOWN"
        if candidate is not None:
            try:
                candidate_state = candidate_profile_service.build_candidate_state(candidate)
                candidate_id = candidate_state.candidate_id
            except Exception:
                candidate_state = None

        # Layer 2: InterviewState (live execution progress)
        interview_state = InterviewState(
            session_id=session_id,
            candidate_id=candidate_id,
            current_turn=0,
            question_count=0,
            conversation=[],
            covered_days=[],
            done=False,
            interview_started=True,
            interview_completed=False,
        )

        # Layer 3: CandidateKnowledgeModel (initialized empty / UNKNOWN)
        knowledge_model = CandidateKnowledgeModel(
            candidate_id=candidate_id,
            topics={}
        )

        # Layer 4: EvidenceLedger (supporting evidence)
        evidence_ledger = EvidenceLedger(
            session_id=session_id,
            items=[]
        )

        session_data: Dict[str, Any] = {
            "session_id": session_id,
            "candidate": candidate,
            "candidate_state": candidate_state,
            "interview_state": interview_state,
            "knowledge_model": knowledge_model,
            "evidence_ledger": evidence_ledger,
            "question_count": 0,
            "conversation": [],
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
        
        # Update Live InterviewState conversation
        if session.get("interview_state"):
            session["interview_state"].conversation.append(message_dict)
            session["interview_state"].current_turn += 1
            
        return True

    def apply_evidence_analysis(
        self, session_id: str, analysis: CandidateEvidenceAnalysis, question_id: str = ""
    ) -> Optional[EvidenceItem]:
        """
        Backend validation and state update layer for LLM analysis.
        
        Takes structured CandidateEvidenceAnalysis, validates it, constructs
        an EvidenceItem for EvidenceLedger, and updates CandidateKnowledgeModel.
        
        IMPORTANT: The LLM returns analysis data only. This backend method executes
        the actual state mutation.
        """
        session = self.get_session(session_id)
        if not session:
            return None

        evidence_ledger: EvidenceLedger = session["evidence_ledger"]
        knowledge_model: CandidateKnowledgeModel = session["knowledge_model"]

        # 1. Construct and record EvidenceItem
        evidence_id = f"ev-{uuid.uuid4().hex[:8]}"
        turn = session["interview_state"].current_turn if session.get("interview_state") else 0

        item = EvidenceItem(
            evidence_id=evidence_id,
            session_id=session_id,
            question_id=question_id or f"q-{turn}",
            candidate_id=knowledge_model.candidate_id,
            curriculum_day=analysis.curriculum_day,
            topic=analysis.topic,
            candidate_claim=analysis.candidate_claim,
            evidence_text=analysis.evidence_text,
            assessment=analysis.assessment_type,
            confidence=analysis.confidence,
            turn=turn,
        )
        evidence_ledger.add_evidence(item)

        # 2. Update CandidateKnowledgeModel for topic
        day = analysis.curriculum_day
        topic_knowledge = knowledge_model.topics.get(
            day,
            CandidateTopicKnowledge(
                curriculum_day=day,
                topic=analysis.topic,
                understanding_level="UNKNOWN",
                confidence=0.0,
                strengths=[],
                gaps=[],
                evidence_ids=[],
            )
        )

        topic_knowledge.understanding_level = analysis.understanding_assessment
        topic_knowledge.confidence = analysis.confidence
        topic_knowledge.strengths = list(set(topic_knowledge.strengths + analysis.strengths))
        topic_knowledge.gaps = list(set(topic_knowledge.gaps + analysis.gaps))
        if evidence_id not in topic_knowledge.evidence_ids:
            topic_knowledge.evidence_ids.append(evidence_id)

        knowledge_model.topics[day] = topic_knowledge
        return item

    def clear_all(self) -> None:
        """Clear all stored sessions. Useful for testing or resetting state."""
        self._sessions.clear()


# Global singleton instance
session_manager = SessionManager()
