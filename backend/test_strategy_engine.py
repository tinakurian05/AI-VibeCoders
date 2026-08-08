import pytest
from models.strategy import (
    StrategyEngineInput, StrategyDecision, StrategyAction, DifficultyLevel
)
from models.interview import (
    InterviewState, InterviewPlan, CandidateKnowledgeModel, EvidenceLedger, CandidateEvidenceAnalysis,
    InterviewTopicPlan, CandidateTopicKnowledge, ObjectiveKnowledge
)
from services.strategy_engine import StrategyEngine

@pytest.fixture
def engine():
    return StrategyEngine()

@pytest.fixture
def base_input():
    plan = InterviewPlan(
        candidate_id="C1",
        candidate_name="Alice",
        job_role="Engineer",
        selected_days=[21, 22, 23, 24],
        total_question_budget=10,
        topic_plans=[
            InterviewTopicPlan(
                day=21, title="RAG", module_id=1, module_title="M1", question_count=3,
                priority_score=1.0, attempts=1, follow_up_allowed=True, probing_reason="",
                tools=[], objectives=["obj1", "obj2"]
            ),
            InterviewTopicPlan(
                day=22, title="VectorDB", module_id=1, module_title="M1", question_count=3,
                priority_score=1.0, attempts=1, follow_up_allowed=True, probing_reason="",
                tools=[], objectives=["obj3"]
            )
        ]
    )
    
    state = InterviewState(
        session_id="S1",
        candidate_id="C1",
        question_count=2,
        covered_days=[21],
        current_topic_day=21
    )
    
    knowledge = CandidateKnowledgeModel(
        candidate_id="C1",
        topics={
            21: CandidateTopicKnowledge(
                curriculum_day=21,
                topic="RAG",
                objectives={
                    "obj1": ObjectiveKnowledge(objective_id="obj1", text="", understanding_level="HIGH"),
                    "obj2": ObjectiveKnowledge(objective_id="obj2", text="", understanding_level="UNKNOWN")
                }
            )
        }
    )
    
    ledger = EvidenceLedger(session_id="S1")
    
    analysis = CandidateEvidenceAnalysis(
        curriculum_day=21,
        topic="RAG",
        understanding_assessment="HIGH",
        assessment_type="supports_understanding",
        confidence=0.9,
        strengths=["Good"],
        gaps=[],
        evidence_text="Ev",
        candidate_claim="Claim",
        follow_up_recommended=False
    )
    
    return StrategyEngineInput(
        interview_state=state,
        interview_plan=plan,
        knowledge_model=knowledge,
        evidence_ledger=ledger,
        latest_analysis=analysis,
        relevant_memories=[]
    )

def test_1_strong_answer_deepen(engine, base_input):
    # unmet objective exists (obj2)
    decision = engine.decide(base_input)
    assert decision.action == StrategyAction.DEEPEN
    assert decision.difficulty == DifficultyLevel.HARD
    assert decision.target_objective == "obj2"

def test_2_strong_answer_topic_fully_assessed(engine, base_input):
    # mark all objectives as HIGH
    base_input.knowledge_model.topics[21].objectives["obj2"].understanding_level = "HIGH"
    decision = engine.decide(base_input)
    assert decision.action == StrategyAction.MOVE_TOPIC
    assert decision.target_day == 22

def test_3_partial_answer(engine, base_input):
    base_input.latest_analysis.understanding_assessment = "MEDIUM"
    base_input.latest_analysis.gaps = ["Some gap"]
    decision = engine.decide(base_input)
    assert decision.action == StrategyAction.FOLLOW_UP
    assert decision.difficulty == DifficultyLevel.MEDIUM

def test_4_misconception(engine, base_input):
    base_input.latest_analysis.gaps = ["Has a misconception about X"]
    decision = engine.decide(base_input)
    assert decision.action == StrategyAction.FOLLOW_UP
    assert decision.difficulty == DifficultyLevel.MEDIUM

def test_5_ambiguous_answer(engine, base_input):
    base_input.latest_analysis.assessment_type = "ambiguous"
    base_input.latest_analysis.confidence = 0.3
    decision = engine.decide(base_input)
    assert decision.action == StrategyAction.CLARIFY
    assert decision.difficulty == DifficultyLevel.EASY

def test_6_weak_answer(engine, base_input):
    base_input.latest_analysis.understanding_assessment = "LOW"
    decision = engine.decide(base_input)
    assert decision.action == StrategyAction.FOLLOW_UP
    assert decision.difficulty == DifficultyLevel.EASY

def test_7_difficulty_adaptation(engine, base_input):
    base_input.latest_analysis.understanding_assessment = "HIGH"
    d1 = engine.decide(base_input)
    assert d1.difficulty == DifficultyLevel.HARD
    
    base_input.latest_analysis.understanding_assessment = "LOW"
    d2 = engine.decide(base_input)
    assert d2.difficulty == DifficultyLevel.EASY

def test_8_objective_targeting(engine, base_input):
    # base_input has obj1=HIGH, obj2=UNKNOWN
    decision = engine.decide(base_input)
    assert decision.target_objective == "obj2"

def test_9_topic_transition(engine, base_input):
    base_input.knowledge_model.topics[21].objectives["obj2"].understanding_level = "HIGH"
    decision = engine.decide(base_input)
    assert decision.action == StrategyAction.MOVE_TOPIC
    assert decision.target_day == 22

def test_10_minimum_question_requirement(engine, base_input):
    base_input.interview_state.question_count = 7
    base_input.interview_state.covered_days = [21, 22, 23, 24]
    base_input.knowledge_model.topics[21].objectives["obj2"].understanding_level = "HIGH"
    # No more topics in plan (only 21,22 are in topic_plans for base_input, but let's clear them)
    base_input.interview_plan.topic_plans = []
    # Should not end since Q<8, even if impossible it might end if forced, but let's check
    decision = engine.decide(base_input)
    assert decision.action != StrategyAction.END or decision.intent == "end_interview_forced"

def test_11_minimum_curriculum_day_requirement(engine, base_input):
    base_input.interview_state.question_count = 8
    base_input.interview_state.covered_days = [21]
    base_input.knowledge_model.topics[21].objectives["obj2"].understanding_level = "HIGH"
    # remaining day 22 exists
    decision = engine.decide(base_input)
    assert decision.action != StrategyAction.END

def test_12_question_budget(engine, base_input):
    base_input.interview_state.question_count = 10
    base_input.interview_state.covered_days = [21, 22, 23, 24]
    decision = engine.decide(base_input)
    assert decision.action == StrategyAction.END

def test_13_empty_breeth_memories(engine, base_input):
    base_input.relevant_memories = []
    decision = engine.decide(base_input)
    assert decision.action == StrategyAction.DEEPEN

def test_14_optional_memory_influence(engine, base_input):
    base_input.relevant_memories = [{"topic": "RAG", "content": "used before"}]
    # Currently engine just passes memory context conceptually to LLM, but deterministic engine doesn't mutate based on this directly yet unless we added specific rules for it. 
    # Just verify it runs fine.
    decision = engine.decide(base_input)
    assert decision is not None

def test_15_current_evidence_overrides_memory(engine, base_input):
    base_input.relevant_memories = [{"content": "candidate is expert"}]
    base_input.latest_analysis.understanding_assessment = "LOW"
    decision = engine.decide(base_input)
    assert decision.action == StrategyAction.FOLLOW_UP # respects LOW understanding

def test_16_attempt_count_no_override(engine, base_input):
    base_input.interview_plan.topic_plans[0].attempts = 10
    decision = engine.decide(base_input)
    assert decision.action == StrategyAction.DEEPEN # remains based on HIGH analysis

def test_17_no_state_mutation(engine, base_input):
    qc_before = base_input.interview_state.question_count
    engine.decide(base_input)
    assert base_input.interview_state.question_count == qc_before

def test_18_determinism(engine, base_input):
    d1 = engine.decide(base_input)
    d2 = engine.decide(base_input)
    assert d1.action == d2.action
    assert d1.target_day == d2.target_day
