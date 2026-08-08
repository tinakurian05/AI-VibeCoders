import json
import pytest
from unittest.mock import Mock

from models.strategy import StrategyDecision, StrategyAction, DifficultyLevel
from models.interview import (
    InterviewState,
    InterviewPlan,
    InterviewTopicPlan,
    CandidateTopicKnowledge,
    EvidenceItem,
    LLMResponse,
)
from models.question_generator import (
    QuestionGeneratorInput,
    GeneratedQuestion,
    QuestionGeneratorError,
    InterviewShouldEnd,
)
from services.question_generator import QuestionGenerator

# Helper to create a dummy LLM gateway that returns a predefined JSON response
def dummy_gateway_factory(json_obj):
    def generate(*, system_prompt, user_prompt, temperature=0.7, model=None, timeout=15.0):
        # Return a successful LLMResponse with the given JSON object as string
        return LLMResponse(
            content=json.dumps(json_obj),
            model_used="dummy-model",
            provider="dummy",
            latency_ms=0.1,
            success=True,
        )
    return Mock(generate=generate)

@pytest.fixture
def base_plan():
    tp1 = InterviewTopicPlan(
        day=21,
        title="RAG",
        module_id=1,
        module_title="M1",
        question_count=3,
        priority_score=1.0,
        attempts=1,
        follow_up_allowed=True,
        probing_reason="",
        tools=[],
        objectives=["obj1", "obj2"],
    )
    tp2 = InterviewTopicPlan(
        day=22,
        title="VectorDB",
        module_id=1,
        module_title="M1",
        question_count=3,
        priority_score=1.0,
        attempts=1,
        follow_up_allowed=True,
        probing_reason="",
        tools=[],
        objectives=["obj3"],
    )
    return InterviewPlan(
        candidate_id="C1",
        candidate_name="Alice",
        job_role="Engineer",
        selected_days=[21, 22],
        total_question_budget=10,
        topic_plans=[tp1, tp2],
    )

@pytest.fixture
def base_state():
    return InterviewState(
        session_id="S1",
        candidate_id="C1",
        question_count=2,
        covered_days=[21],
        current_topic_day=21,
    )

def test_deepen_generates_hard_question(base_plan, base_state):
    decision = StrategyDecision(
        action=StrategyAction.DEEPEN,
        target_day=21,
        target_objective="obj2",
        difficulty=DifficultyLevel.HARD,
        intent="probe retrieval evaluation",
        reasoning="candidate understands basics",
        follow_up=True,
        should_end=False,
    )
    input_data = QuestionGeneratorInput(
        candidate_id="C1",
        strategy_decision=decision,
        interview_state=base_state,
        interview_plan=base_plan,
        recent_evidence=[
            EvidenceItem(
                evidence_id="e1",
                session_id="S1",
                question_id="q1",
                candidate_id="C1",
                curriculum_day=21,
                topic="RAG",
                objective_id="obj2",
                candidate_claim="I use BM25",
                evidence_text="Explained BM25 basics",
                assessment="supports_understanding",
                confidence=0.9,
                turn=1,
            )
        ],
    )
    # LLM mock returns a HARD question matching difficulty
    mock_resp = {
        "question_id": "qid-1",
        "question": "How would you evaluate retrieval performance when the collection scales to millions of documents?",
        "target_day": 21,
        "target_objective": "obj2",
        "difficulty": "HARD",
        "intent": "probe retrieval evaluation",
    }
    gateway = dummy_gateway_factory(mock_resp)
    qgen = QuestionGenerator(gateway=gateway)
    generated = qgen.generate(input_data)
    assert isinstance(generated, GeneratedQuestion)
    assert generated.difficulty == DifficultyLevel.HARD
    assert generated.target_day == 21
    assert generated.target_objective == "obj2"
    assert generated.question_id == "qid-1"

def test_follow_up_uses_recent_evidence(base_plan, base_state):
    decision = StrategyDecision(
        action=StrategyAction.FOLLOW_UP,
        target_day=21,
        target_objective="obj1",
        difficulty=DifficultyLevel.MEDIUM,
        intent="clarify claim",
        reasoning="candidate mentioned ChromaDB",
        follow_up=True,
        should_end=False,
    )
    evidence = EvidenceItem(
        evidence_id="e2",
        session_id="S1",
        question_id="q2",
        candidate_id="C1",
        curriculum_day=21,
        topic="RAG",
        objective_id="obj1",
        candidate_claim="I used ChromaDB because it runs locally",
        evidence_text="ChromaDB local simplicity",
        assessment="supports_understanding",
        confidence=0.85,
        turn=2,
    )
    input_data = QuestionGeneratorInput(
        candidate_id="C1",
        strategy_decision=decision,
        interview_state=base_state,
        interview_plan=base_plan,
        recent_evidence=[evidence],
    )
    mock_resp = {
        "question_id": "qid-2",
        "question": "You mentioned ChromaDB for local simplicity. How would you adapt it for a production environment with massive scale?",
        "target_day": 21,
        "target_objective": "obj1",
        "difficulty": "MEDIUM",
        "intent": "clarify claim",
    }
    gateway = dummy_gateway_factory(mock_resp)
    qgen = QuestionGenerator(gateway=gateway)
    generated = qgen.generate(input_data)
    assert "ChromaDB" in generated.question
    assert generated.difficulty == DifficultyLevel.MEDIUM

def test_clarify_question_generated(base_plan, base_state):
    decision = StrategyDecision(
        action=StrategyAction.CLARIFY,
        target_day=22,
        target_objective=None,
        difficulty=DifficultyLevel.EASY,
        intent="clarify ambiguous answer",
        reasoning="candidate was vague",
        follow_up=True,
        should_end=False,
    )
    input_data = QuestionGeneratorInput(
        candidate_id="C1",
        strategy_decision=decision,
        interview_state=base_state,
        interview_plan=base_plan,
        recent_conversation=[{"role": "assistant", "content": "Explain vector search."}, {"role": "candidate", "content": "I think it's about similarity."}],
    )
    mock_resp = {
        "question_id": "qid-3",
        "question": "Could you elaborate on what you mean by \"similarity\" in the context of vector search?",
        "target_day": 22,
        "target_objective": None,
        "difficulty": "EASY",
        "intent": "clarify ambiguous answer",
    }
    gateway = dummy_gateway_factory(mock_resp)
    qgen = QuestionGenerator(gateway=gateway)
    generated = qgen.generate(input_data)
    assert "elaborate" in generated.question.lower()
    assert generated.difficulty == DifficultyLevel.EASY

def test_move_topic_generates_new_topic_question(base_plan, base_state):
    decision = StrategyDecision(
        action=StrategyAction.MOVE_TOPIC,
        target_day=22,
        target_objective=None,
        difficulty=DifficultyLevel.MEDIUM,
        intent="probe new topic",
        reasoning="switching",
        follow_up=False,
        should_end=False,
    )
    input_data = QuestionGeneratorInput(
        candidate_id="C1",
        strategy_decision=decision,
        interview_state=base_state,
        interview_plan=base_plan,
    )
    mock_resp = {
        "question_id": "qid-4",
        "question": "Let's talk about Vector Databases. What are the main trade‑offs between exact and approximate nearest‑neighbor search?",
        "target_day": 22,
        "target_objective": None,
        "difficulty": "MEDIUM",
        "intent": "probe new topic",
    }
    gateway = dummy_gateway_factory(mock_resp)
    qgen = QuestionGenerator(gateway=gateway)
    generated = qgen.generate(input_data)
    assert "Vector Databases" in generated.question
    assert generated.target_day == 22

def test_end_raises_interviewshouldend(base_plan, base_state):
    decision = StrategyDecision(
        action=StrategyAction.END,
        target_day=21,
        target_objective=None,
        difficulty=DifficultyLevel.MEDIUM,
        intent="end_interview",
        reasoning="budget met",
        follow_up=False,
        should_end=True,
    )
    input_data = QuestionGeneratorInput(
        candidate_id="C1",
        strategy_decision=decision,
        interview_state=base_state,
        interview_plan=base_plan,
    )
    qgen = QuestionGenerator()
    with pytest.raises(InterviewShouldEnd):
        qgen.generate(input_data)

def test_invalid_json_raises_error(base_plan, base_state):
    decision = StrategyDecision(
        action=StrategyAction.FOLLOW_UP,
        target_day=21,
        target_objective="obj1",
        difficulty=DifficultyLevel.MEDIUM,
        intent="test",
        reasoning="",
        follow_up=True,
        should_end=False,
    )
    input_data = QuestionGeneratorInput(
        candidate_id="C1",
        strategy_decision=decision,
        interview_state=base_state,
        interview_plan=base_plan,
    )
    # Return malformed JSON
    malformed = "{ not a json }"
    def generate(*, system_prompt, user_prompt, temperature=0.7, model=None, timeout=15.0):
        return LLMResponse(content=malformed, model_used="dummy", provider="dummy", latency_ms=0.1, success=True)
    gateway = Mock(generate=generate)
    qgen = QuestionGenerator(gateway=gateway)
    with pytest.raises(QuestionGeneratorError):
        qgen.generate(input_data)

def test_memories_are_included_without_overriding(base_plan, base_state):
    decision = StrategyDecision(
        action=StrategyAction.FOLLOW_UP,
        target_day=21,
        target_objective="obj1",
        difficulty=DifficultyLevel.MEDIUM,
        intent="use memory context",
        reasoning="test",
        follow_up=True,
        should_end=False,
    )
    input_data = QuestionGeneratorInput(
        candidate_id="C1",
        strategy_decision=decision,
        interview_state=base_state,
        interview_plan=base_plan,
        recent_evidence=[],
        relevant_memories=[{"topic": "RAG", "note": "candidate previously built a retrieval system"}],
    )
    mock_resp = {
        "question_id": "qid-5",
        "question": "Given your experience building a retrieval system, how would you handle out‑of‑vocabulary queries?",
        "target_day": 21,
        "target_objective": "obj1",
        "difficulty": "MEDIUM",
        "intent": "use memory context",
    }
    gateway = dummy_gateway_factory(mock_resp)
    qgen = QuestionGenerator(gateway=gateway)
    generated = qgen.generate(input_data)
    assert "out‑of‑vocabulary" in generated.question.lower()
    assert generated.difficulty == DifficultyLevel.MEDIUM
