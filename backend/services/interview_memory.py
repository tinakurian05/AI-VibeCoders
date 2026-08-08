from typing import Optional, Dict, Any, List
from models.interview import CandidateEvidenceAnalysis
from services.memory_service import memory_service, MemoryService


class InterviewMemoryService:
    """
    Application-level boundary service for managing interview session memories
    via the underlying Breeth MemoryService (memory_service.py).
    
    Provides clean retrieval and turn-storing APIs for the Interview Engine
    while strictly delegating network operations and ensuring state boundaries.
    
    IMPORTANT:
    - This service does NOT directly mutate CandidateState, InterviewState,
      CandidateKnowledgeModel, or EvidenceLedger.
    - All memory operations fail gracefully without raising exceptions.
    - Credentials and secrets are never exposed in returns or errors.
    """

    def __init__(self, mem_service: Optional[MemoryService] = None) -> None:
        self._memory_service = mem_service or memory_service

    def get_relevant_memories(
        self,
        session_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for an interview session given a query.
        
        Delegates to MemoryService.search_memory().
        Returns [] if Breeth is unconfigured, timed out, or unavailable.
        """
        if not session_id or not query:
            return []

        try:
            results = self._memory_service.search_memory(
                session_id=session_id,
                query=query,
                limit=limit
            )
            if isinstance(results, list):
                return results
            return []
        except Exception:
            # Failure fallback: memory search error should never break the interview
            return []

    def store_turn(
        self,
        session_id: str,
        turn_number: int,
        question: str,
        candidate_answer: str,
        curriculum_day: Optional[int] = None,
        topic: Optional[str] = None,
        analysis: Optional[CandidateEvidenceAnalysis] = None
    ) -> Dict[str, Any]:
        """
        Store an interview turn (question + candidate answer + optional analysis) as a memory episode.
        
        Delegates to MemoryService.store_episode().
        Returns structured dictionary indicating result without raising exceptions on failure.
        """
        if not session_id:
            return {"success": False, "status": "error", "message": "session_id is required"}

        messages = [
            {"role": "interviewer", "content": question},
            {"role": "candidate", "content": candidate_answer}
        ]

        metadata: Dict[str, Any] = {
            "session_id": session_id,
            "turn_number": turn_number,
            "curriculum_day": curriculum_day,
            "topic": topic
        }

        if analysis is not None:
            metadata["understanding_assessment"] = analysis.understanding_assessment
            metadata["assessment_type"] = analysis.assessment_type
            metadata["strengths"] = analysis.strengths
            metadata["gaps"] = analysis.gaps
            metadata["evidence_text"] = analysis.evidence_text
            metadata["candidate_claim"] = analysis.candidate_claim
            metadata["follow_up_recommended"] = analysis.follow_up_recommended

        try:
            res = self._memory_service.store_episode(
                session_id=session_id,
                messages=messages,
                metadata=metadata
            )
            if isinstance(res, dict):
                return res
            return {"success": True, "data": res}
        except Exception as e:
            # Fallback safely: episode storage failure should never break caller
            return {
                "success": False,
                "status": "error",
                "message": "Failed to store turn episode"
            }


# Default global instance
interview_memory_service = InterviewMemoryService()
