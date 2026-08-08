from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from models.interview import CandidateTopicKnowledge

class AnalyzerError(Exception):
    """Exception raised when the AnswerAnalyzer fails to process or validate an analysis."""
    pass

class AnswerAnalyzerInput(BaseModel):
    """Input payload for the Answer Analyzer."""
    candidate_id: str
    current_question: str
    candidate_answer: str
    curriculum_day: int
    topic: str
    relevant_objectives: List[str]
    current_topic_knowledge: CandidateTopicKnowledge
    conversation_history: List[Dict[str, str]]
    relevant_memories: List[Dict[str, Any]] = []
