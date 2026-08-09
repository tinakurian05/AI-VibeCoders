"""
Integration tests for InterviewOrchestrator.

All tests use mocked LLM gateway / services to verify orchestration
logic, state transitions, and service coordination — NOT LLM quality.
"""
import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from models.interview import (
    InterviewState,
    InterviewPlan,
    InterviewTopicPlan,
    InterviewResponse,
    CandidateKnowledgeModel,
    CandidateTopicKnowledge,
    ObjectiveKnowledge,
    EvidenceLedger,
    CandidateEvidenceAnalysis,
    LLMResponse,
)
from models.strategy import (
    StrategyEngineInput,
    StrategyDecision,
    StrategyAction,
    DifficultyLevel,
)
from models.question_generator import (
    QuestionGeneratorInput,
    GeneratedQuestion,
    QuestionGeneratorError,
    InterviewShouldEnd,
)
from models.analyzer import AnswerAnalyzerInput, AnalyzerError
from services.session_manager import SessionManager
from services.answer_analyzer import AnswerAnalyzer
from services.strategy_engine import StrategyEngine
from services.question_generator import QuestionGenerator
from services.interview_orchestrator import InterviewOrchestrator, OrchestratorError


# ======================================================================
# Fixtures
# ======================================================================

def _make_plan():
    """Build a realistic InterviewPlan with 2 topics and 10 question budget."""
    return InterviewPlan(
        candidate_id="C1",
        candidate_name="Alice",
        job_role="Engineer",
        selected_days=[21, 22],
        total_question_budget=10,
        topic_plans=[
            InterviewTopicPlan(
                day=21,
                title="RAG Fundamentals",
                module_id=1,
                module_title="Module 1",
                question_count=5,
                priority_score=12.0,
                attempts=1,
                follow_up_allowed=True,
                probing_reason="Core topic",
                tools=["LangChain"],
                objectives=[
                    "Understand RAG architecture",
                    "Explain retrieval vs generation",
                ],
            ),
            InterviewTopicPlan(
                day=22,
                title="Vector Databases",
                module_id=2,
                module_title="Module 2",
                question_count=5,
                priority_score=11.0,
                attempts=1,
                follow_up_allowed=True,
                probing_reason="Core topic",
                tools=["ChromaDB"],
                objectives=[
                    "Understand vector similarity search",
                ],
            ),
        ],
    )


def _make_knowledge_model():
    """Build a CandidateKnowledgeModel matching the plan."""
    return CandidateKnowledgeModel(
        candidate_id="C1",
        topics={
            21: CandidateTopicKnowledge(
                curriculum_day=21,
                topic="RAG Fundamentals",
                understanding_level="UNKNOWN",
                objectives={
                    "day-21-obj-0": ObjectiveKnowledge(
                        objective_id="day-21-obj-0",
                        text="Understand RAG architecture",
                    ),
                    "day-21-obj-1": ObjectiveKnowledge(
                        objective_id="day-21-obj-1",
                        text="Explain retrieval vs generation",
                    ),
                },
            ),
            22: CandidateTopicKnowledge(
                curriculum_day=22,
                topic="Vector Databases",
                understanding_level="UNKNOWN",
                objectives={
                    "day-22-obj-0": ObjectiveKnowledge(
                        objective_id="day-22-obj-0",
                        text="Understand vector similarity search",
                    ),
                },
            ),
        },
    )


def _make_session(session_id="S1"):
    """Build a complete session dict matching what SessionManager.create_session produces."""
    plan = _make_plan()
    knowledge_model = _make_knowledge_model()

    interview_state = InterviewState(
        session_id=session_id,
        candidate_id="C1",
        current_turn=0,
        question_count=0,
        interview_plan=plan,
        current_question=None,
        conversation=[],
        covered_days=[],
        completed_question_ids=[],
        current_topic_day=None,
        done=False,
        interview_started=True,
        interview_completed=False,
    )

    return {
        "session_id": session_id,
        "candidate": {},
        "candidate_state": None,
        "interview_state": interview_state,
        "knowledge_model": knowledge_model,
        "evidence_ledger": EvidenceLedger(session_id=session_id),
        "question_count": 0,
        "conversation": [],
        "done": False,
    }


def _mock_generated_question(
    question_id="q-1",
    question="Explain how RAG combines retrieval and generation.",
    target_day=21,
    target_objective="day-21-obj-0",
    difficulty=DifficultyLevel.MEDIUM,
    intent="initial_topic_probe",
):
    return GeneratedQuestion(
        question_id=question_id,
        question=question,
        target_day=target_day,
        target_objective=target_objective,
        difficulty=difficulty,
        intent=intent,
    )


def _mock_analysis(
    curriculum_day=21,
    topic="RAG Fundamentals",
    understanding="MEDIUM",
    assessment_type="supports_understanding",
    confidence=0.7,
    strengths=None,
    gaps=None,
    follow_up=True,
):
    return CandidateEvidenceAnalysis(
        curriculum_day=curriculum_day,
        topic=topic,
        understanding_assessment=understanding,
        assessment_type=assessment_type,
        confidence=confidence,
        strengths=strengths or ["Partial understanding"],
        gaps=gaps or ["Missing depth"],
        evidence_text="Candidate demonstrated partial knowledge",
        candidate_claim="RAG uses retrieval",
        follow_up_recommended=follow_up,
    )


def _build_orchestrator(session_dict, qgen_return=None, analyzer_return=None, strategy_return=None):
    """Build an InterviewOrchestrator with mocked services."""
    # SessionManager mock
    mock_sm = MagicMock(spec=SessionManager)
    mock_sm.get_session.return_value = session_dict
    mock_sm.session_exists.return_value = True
    mock_sm.add_message.return_value = True
    mock_sm.apply_evidence_analysis.return_value = MagicMock()

    # AnswerAnalyzer mock
    mock_analyzer = MagicMock(spec=AnswerAnalyzer)
    if analyzer_return is not None:
        mock_analyzer.analyze_with_memory.return_value = analyzer_return

    # StrategyEngine — use real engine by default unless override provided
    if strategy_return is not None:
        mock_strategy = MagicMock(spec=StrategyEngine)
        mock_strategy.decide.return_value = strategy_return
    else:
        mock_strategy = StrategyEngine()

    # QuestionGenerator mock
    mock_qgen = MagicMock(spec=QuestionGenerator)
    if qgen_return is not None:
        mock_qgen.generate.return_value = qgen_return

    orchestrator = InterviewOrchestrator(
        session_mgr=mock_sm,
        analyzer=mock_analyzer,
        strategy=mock_strategy,
        qgen=mock_qgen,
    )

    return orchestrator, mock_sm, mock_analyzer, mock_strategy, mock_qgen


# ======================================================================
# Test 1: Start Interview
# ======================================================================

class TestStartInterview:
    def test_start_creates_first_question(self):
        """Session created → first question generated → current_question populated → done=False."""
        session = _make_session()
        generated = _mock_generated_question()

        orch, mock_sm, _, _, mock_qgen = _build_orchestrator(session, qgen_return=generated)

        response = orch.start_interview("S1")

        assert isinstance(response, InterviewResponse)
        assert response.done is False
        assert response.reply == generated.question
        assert len(response.reply) > 0

        # Verify state was updated
        state = session["interview_state"]
        assert state.current_question == generated.question
        assert state.current_question_meta is not None
        assert state.current_question_meta["question_id"] == "q-1"
        assert state.current_question_meta["target_day"] == 21
        assert state.current_question_meta["target_objective"] == "day-21-obj-0"
        assert state.question_count == 1
        assert state.current_topic_day == 21

        # Verify question generator was called
        mock_qgen.generate.assert_called_once()

        # Verify assistant message was recorded
        mock_sm.add_message.assert_called_once_with("S1", "assistant", generated.question)

    def test_start_without_plan_raises(self):
        """Session without interview plan → OrchestratorError."""
        session = _make_session()
        session["interview_state"].interview_plan = None

        orch, _, _, _, _ = _build_orchestrator(session)

        with pytest.raises(OrchestratorError, match="no interview plan"):
            orch.start_interview("S1")

    def test_start_missing_session_raises(self):
        """Nonexistent session → OrchestratorError."""
        session = _make_session()
        orch, mock_sm, _, _, _ = _build_orchestrator(session)
        mock_sm.get_session.return_value = None

        with pytest.raises(OrchestratorError, match="not found"):
            orch.start_interview("nonexistent")


# ======================================================================
# Test 2: Process One Answer
# ======================================================================

class TestProcessAnswer:
    def _setup_session_with_question(self):
        """Return a session that has a current question (as if start_interview was called)."""
        session = _make_session()
        state = session["interview_state"]
        state.current_question = "Explain how RAG combines retrieval and generation."
        state.current_question_meta = {
            "question_id": "q-1",
            "target_day": 21,
            "target_objective": "day-21-obj-0",
            "difficulty": "MEDIUM",
            "intent": "initial_topic_probe",
        }
        state.current_topic_day = 21
        state.question_count = 1
        return session

    def test_full_answer_pipeline(self):
        """Candidate answer → AnswerAnalyzer → apply_evidence → StrategyEngine → QuestionGenerator → next question."""
        session = self._setup_session_with_question()
        analysis = _mock_analysis()
        next_q = _mock_generated_question(
            question_id="q-2",
            question="How would you handle chunking?",
            target_objective="day-21-obj-0",
            intent="address_specific_gap",
        )

        # Strategy: follow up on same topic
        strategy_decision = StrategyDecision(
            action=StrategyAction.FOLLOW_UP,
            target_day=21,
            target_objective="day-21-obj-0",
            difficulty=DifficultyLevel.MEDIUM,
            intent="address_specific_gap",
            reasoning="Partial understanding",
            follow_up=True,
            should_end=False,
        )

        orch, mock_sm, mock_analyzer, mock_strategy, mock_qgen = _build_orchestrator(
            session,
            analyzer_return=analysis,
            strategy_return=strategy_decision,
            qgen_return=next_q,
        )

        response = orch.process_answer("S1", "RAG uses vector search for retrieval.")

        assert response.done is False
        assert response.reply == "How would you handle chunking?"

        # Verify analyzer was called
        mock_analyzer.analyze_with_memory.assert_called_once()
        call_args = mock_analyzer.analyze_with_memory.call_args
        assert call_args.kwargs["session_id"] == "S1"
        assert call_args.kwargs["turn_number"] == 1

        # Verify evidence was applied
        mock_sm.apply_evidence_analysis.assert_called_once()
        ea_call = mock_sm.apply_evidence_analysis.call_args
        assert ea_call.kwargs["session_id"] == "S1"
        assert ea_call.kwargs["question_id"] == "q-1"
        assert ea_call.kwargs["objective_id"] == "day-21-obj-0"

        # Verify strategy was called
        mock_strategy.decide.assert_called_once()

        # Verify next question was generated
        mock_qgen.generate.assert_called_once()

        # Verify state update
        state = session["interview_state"]
        assert state.current_question == "How would you handle chunking?"
        assert state.question_count == 2
        assert "q-1" in state.completed_question_ids


# ======================================================================
# Test 3: Objective Traceability
# ======================================================================

class TestObjectiveTraceability:
    def test_objective_flows_from_question_to_evidence(self):
        """GeneratedQuestion.target_objective → apply_evidence_analysis(objective_id=...) → correct path."""
        session = _make_session()
        state = session["interview_state"]
        state.current_question = "Explain RAG architecture."
        state.current_question_meta = {
            "question_id": "q-trace",
            "target_day": 21,
            "target_objective": "day-21-obj-1",
            "difficulty": "MEDIUM",
            "intent": "probe",
        }
        state.current_topic_day = 21
        state.question_count = 1

        analysis = _mock_analysis()
        next_q = _mock_generated_question(question_id="q-trace-2")

        strategy_decision = StrategyDecision(
            action=StrategyAction.FOLLOW_UP,
            target_day=21,
            target_objective="day-21-obj-1",
            difficulty=DifficultyLevel.MEDIUM,
            intent="follow_up",
            reasoning="",
            follow_up=True,
            should_end=False,
        )

        orch, mock_sm, _, _, _ = _build_orchestrator(
            session,
            analyzer_return=analysis,
            strategy_return=strategy_decision,
            qgen_return=next_q,
        )

        orch.process_answer("S1", "The architecture has a retriever and generator.")

        # Verify the objective_id passed to apply_evidence_analysis matches
        ea_call = mock_sm.apply_evidence_analysis.call_args
        assert ea_call.kwargs["objective_id"] == "day-21-obj-1"


# ======================================================================
# Test 4: Breeth Not Duplicated
# ======================================================================

class TestBreethIntegration:
    def test_analyze_with_memory_called_once(self):
        """Verify analyze_with_memory is called exactly once — no duplicate Breeth ops."""
        session = _make_session()
        state = session["interview_state"]
        state.current_question = "What is RAG?"
        state.current_question_meta = {
            "question_id": "q-b1",
            "target_day": 21,
            "target_objective": "day-21-obj-0",
            "difficulty": "MEDIUM",
            "intent": "probe",
        }
        state.current_topic_day = 21
        state.question_count = 1

        analysis = _mock_analysis()
        next_q = _mock_generated_question(question_id="q-b2")
        strategy_decision = StrategyDecision(
            action=StrategyAction.FOLLOW_UP,
            target_day=21,
            target_objective="day-21-obj-0",
            difficulty=DifficultyLevel.MEDIUM,
            intent="follow",
            reasoning="",
            follow_up=True,
            should_end=False,
        )

        orch, mock_sm, mock_analyzer, _, _ = _build_orchestrator(
            session,
            analyzer_return=analysis,
            strategy_return=strategy_decision,
            qgen_return=next_q,
        )

        orch.process_answer("S1", "RAG retrieves documents")

        # analyze_with_memory called exactly once
        assert mock_analyzer.analyze_with_memory.call_count == 1

        # Orchestrator never calls memory service directly (no attribute access)
        assert not hasattr(orch, 'memory_service')


# ======================================================================
# Test 5: Strategy END
# ======================================================================

class TestStrategyEnd:
    def test_should_end_completes_interview(self):
        """StrategyDecision.should_end=True → QuestionGenerator NOT called → done=True."""
        session = _make_session()
        state = session["interview_state"]
        state.current_question = "Explain RAG."
        state.current_question_meta = {
            "question_id": "q-end",
            "target_day": 21,
            "target_objective": "day-21-obj-0",
            "difficulty": "MEDIUM",
            "intent": "probe",
        }
        state.current_topic_day = 21
        state.question_count = 1

        analysis = _mock_analysis()
        end_decision = StrategyDecision(
            action=StrategyAction.END,
            target_day=21,
            target_objective=None,
            difficulty=DifficultyLevel.MEDIUM,
            intent="end_interview",
            reasoning="Budget met",
            follow_up=False,
            should_end=True,
        )

        orch, _, _, _, mock_qgen = _build_orchestrator(
            session,
            analyzer_return=analysis,
            strategy_return=end_decision,
        )

        response = orch.process_answer("S1", "My final answer.")

        assert response.done is True
        assert state.done is True
        assert state.interview_completed is True

        # QuestionGenerator must NOT be called
        mock_qgen.generate.assert_not_called()


# ======================================================================
# Test 6: Question Budget
# ======================================================================

class TestQuestionBudget:
    def test_budget_exhausted_ends_interview(self):
        """When question_count >= total_question_budget, interview ends without generating more."""
        session = _make_session()
        state = session["interview_state"]
        state.current_question = "Final question."
        state.current_question_meta = {
            "question_id": "q-budget",
            "target_day": 21,
            "target_objective": "day-21-obj-0",
            "difficulty": "MEDIUM",
            "intent": "probe",
        }
        state.current_topic_day = 21
        state.question_count = 10  # Budget is 10, so this means budget reached

        analysis = _mock_analysis()

        orch, _, _, _, mock_qgen = _build_orchestrator(
            session,
            analyzer_return=analysis,
        )

        response = orch.process_answer("S1", "My answer")

        assert response.done is True
        assert state.done is True
        assert state.interview_completed is True

        # QuestionGenerator must NOT be called
        mock_qgen.generate.assert_not_called()


# ======================================================================
# Test 7: Missing Session
# ======================================================================

class TestMissingSession:
    def test_process_answer_missing_session(self):
        """Nonexistent session → OrchestratorError with 'not found'."""
        session = _make_session()
        orch, mock_sm, _, _, _ = _build_orchestrator(session)
        mock_sm.get_session.return_value = None

        with pytest.raises(OrchestratorError, match="not found"):
            orch.process_answer("nonexistent", "hello")


# ======================================================================
# Test 8: Completed Interview
# ======================================================================

class TestCompletedInterview:
    def test_answer_after_completion_raises(self):
        """Sending answer after interview_completed → OrchestratorError."""
        session = _make_session()
        state = session["interview_state"]
        state.done = True
        state.interview_completed = True
        state.current_question = "Already done."

        orch, _, _, _, _ = _build_orchestrator(session)

        with pytest.raises(OrchestratorError, match="already completed"):
            orch.process_answer("S1", "Another answer")


# ======================================================================
# Test 9: LLM Failure
# ======================================================================

class TestLLMFailure:
    def test_analyzer_failure_raises(self):
        """AnswerAnalyzer failure → OrchestratorError, no fabricated question."""
        session = _make_session()
        state = session["interview_state"]
        state.current_question = "Explain RAG."
        state.current_question_meta = {
            "question_id": "q-fail",
            "target_day": 21,
            "target_objective": "day-21-obj-0",
            "difficulty": "MEDIUM",
            "intent": "probe",
        }
        state.current_topic_day = 21
        state.question_count = 1

        orch, _, mock_analyzer, _, mock_qgen = _build_orchestrator(session)
        mock_analyzer.analyze_with_memory.side_effect = AnalyzerError("LLM generation failed")

        with pytest.raises(OrchestratorError, match="analysis failed"):
            orch.process_answer("S1", "My answer")

        # Question generator must NOT be called
        mock_qgen.generate.assert_not_called()

    def test_qgen_failure_raises(self):
        """QuestionGenerator failure → OrchestratorError, no fabricated question."""
        session = _make_session()
        state = session["interview_state"]
        state.current_question = "Explain RAG."
        state.current_question_meta = {
            "question_id": "q-fail2",
            "target_day": 21,
            "target_objective": "day-21-obj-0",
            "difficulty": "MEDIUM",
            "intent": "probe",
        }
        state.current_topic_day = 21
        state.question_count = 1

        analysis = _mock_analysis()
        strategy_decision = StrategyDecision(
            action=StrategyAction.FOLLOW_UP,
            target_day=21,
            target_objective="day-21-obj-0",
            difficulty=DifficultyLevel.MEDIUM,
            intent="follow",
            reasoning="",
            follow_up=True,
            should_end=False,
        )

        orch, _, _, _, mock_qgen = _build_orchestrator(
            session,
            analyzer_return=analysis,
            strategy_return=strategy_decision,
        )
        mock_qgen.generate.side_effect = QuestionGeneratorError("LLM call failed")

        with pytest.raises(OrchestratorError, match="generation failed"):
            orch.process_answer("S1", "My answer")


# ======================================================================
# Test 10: Multi-Turn State Consistency
# ======================================================================

class TestMultiTurnState:
    def test_three_turns_state_remains_consistent(self):
        """Run 3 turns and verify counters stay consistent."""
        session = _make_session()

        # Set up initial question
        state = session["interview_state"]
        state.current_question = "What is RAG?"
        state.current_question_meta = {
            "question_id": "q-turn-1",
            "target_day": 21,
            "target_objective": "day-21-obj-0",
            "difficulty": "MEDIUM",
            "intent": "initial_topic_probe",
        }
        state.current_topic_day = 21
        state.question_count = 1

        analysis = _mock_analysis()
        follow_decision = StrategyDecision(
            action=StrategyAction.FOLLOW_UP,
            target_day=21,
            target_objective="day-21-obj-0",
            difficulty=DifficultyLevel.MEDIUM,
            intent="follow_up",
            reasoning="",
            follow_up=True,
            should_end=False,
        )

        questions = [
            _mock_generated_question(question_id="q-turn-2", question="Q2?"),
            _mock_generated_question(question_id="q-turn-3", question="Q3?"),
            _mock_generated_question(question_id="q-turn-4", question="Q4?"),
        ]

        mock_sm = MagicMock(spec=SessionManager)
        mock_sm.get_session.return_value = session
        mock_sm.session_exists.return_value = True
        mock_sm.add_message.return_value = True
        mock_sm.apply_evidence_analysis.return_value = MagicMock()

        mock_analyzer = MagicMock(spec=AnswerAnalyzer)
        mock_analyzer.analyze_with_memory.return_value = analysis

        mock_strategy = MagicMock(spec=StrategyEngine)
        mock_strategy.decide.return_value = follow_decision

        mock_qgen = MagicMock(spec=QuestionGenerator)
        mock_qgen.generate.side_effect = questions

        orch = InterviewOrchestrator(
            session_mgr=mock_sm,
            analyzer=mock_analyzer,
            strategy=mock_strategy,
            qgen=mock_qgen,
        )

        # Turn 1
        resp1 = orch.process_answer("S1", "Answer 1")
        assert resp1.done is False
        assert state.question_count == 2
        assert state.current_question == "Q2?"
        assert len(state.completed_question_ids) == 1

        # Turn 2
        resp2 = orch.process_answer("S1", "Answer 2")
        assert resp2.done is False
        assert state.question_count == 3
        assert state.current_question == "Q3?"
        assert len(state.completed_question_ids) == 2

        # Turn 3
        resp3 = orch.process_answer("S1", "Answer 3")
        assert resp3.done is False
        assert state.question_count == 4
        assert state.current_question == "Q4?"
        assert len(state.completed_question_ids) == 3

        # Verify interview is still active
        assert state.done is False
        assert state.interview_completed is False


# ======================================================================
# Test 11: No Duplicate Conversation Messages
# ======================================================================

class TestConversationConsistency:
    def test_single_user_message_per_answer(self):
        """Each candidate answer results in exactly one 'user' add_message call."""
        session = _make_session()
        state = session["interview_state"]
        state.current_question = "What is RAG?"
        state.current_question_meta = {
            "question_id": "q-conv",
            "target_day": 21,
            "target_objective": "day-21-obj-0",
            "difficulty": "MEDIUM",
            "intent": "probe",
        }
        state.current_topic_day = 21
        state.question_count = 1

        analysis = _mock_analysis()
        next_q = _mock_generated_question(question_id="q-conv-2")
        strategy_decision = StrategyDecision(
            action=StrategyAction.FOLLOW_UP,
            target_day=21,
            target_objective="day-21-obj-0",
            difficulty=DifficultyLevel.MEDIUM,
            intent="follow",
            reasoning="",
            follow_up=True,
            should_end=False,
        )

        orch, mock_sm, _, _, _ = _build_orchestrator(
            session,
            analyzer_return=analysis,
            strategy_return=strategy_decision,
            qgen_return=next_q,
        )

        orch.process_answer("S1", "My answer")

        # Check add_message calls
        user_calls = [
            c for c in mock_sm.add_message.call_args_list
            if c.args[1] == "user"
        ]
        assistant_calls = [
            c for c in mock_sm.add_message.call_args_list
            if c.args[1] == "assistant"
        ]

        assert len(user_calls) == 1, f"Expected 1 user message, got {len(user_calls)}"
        assert len(assistant_calls) == 1, f"Expected 1 assistant message, got {len(assistant_calls)}"

        # Verify content
        assert user_calls[0].args[2] == "My answer"
        assert assistant_calls[0].args[2] == next_q.question


# ======================================================================
# Test 12: State Mutation Boundary
# ======================================================================

class TestStateMutationBoundary:
    def test_orchestrator_delegates_mutation_to_session_manager(self):
        """Orchestrator calls SessionManager.apply_evidence_analysis rather than directly modifying models."""
        session = _make_session()
        state = session["interview_state"]
        state.current_question = "What is RAG?"
        state.current_question_meta = {
            "question_id": "q-mut",
            "target_day": 21,
            "target_objective": "day-21-obj-0",
            "difficulty": "MEDIUM",
            "intent": "probe",
        }
        state.current_topic_day = 21
        state.question_count = 1

        analysis = _mock_analysis()
        next_q = _mock_generated_question(question_id="q-mut-2")
        strategy_decision = StrategyDecision(
            action=StrategyAction.FOLLOW_UP,
            target_day=21,
            target_objective="day-21-obj-0",
            difficulty=DifficultyLevel.MEDIUM,
            intent="follow",
            reasoning="",
            follow_up=True,
            should_end=False,
        )

        orch, mock_sm, _, _, _ = _build_orchestrator(
            session,
            analyzer_return=analysis,
            strategy_return=strategy_decision,
            qgen_return=next_q,
        )

        orch.process_answer("S1", "My answer")

        # apply_evidence_analysis must be called
        mock_sm.apply_evidence_analysis.assert_called_once()

        # Verify correct arguments
        call_kwargs = mock_sm.apply_evidence_analysis.call_args.kwargs
        assert call_kwargs["session_id"] == "S1"
        assert call_kwargs["analysis"] == analysis
        assert call_kwargs["question_id"] == "q-mut"
        assert call_kwargs["objective_id"] == "day-21-obj-0"


# ======================================================================
# Test: Covered Days on MOVE_TOPIC
# ======================================================================

class TestCoveredDays:
    def test_move_topic_marks_previous_day_covered(self):
        """When strategy returns MOVE_TOPIC, the previous current_topic_day is added to covered_days."""
        session = _make_session()
        state = session["interview_state"]
        state.current_question = "Explain RAG."
        state.current_question_meta = {
            "question_id": "q-cov",
            "target_day": 21,
            "target_objective": "day-21-obj-0",
            "difficulty": "MEDIUM",
            "intent": "probe",
        }
        state.current_topic_day = 21
        state.question_count = 1

        analysis = _mock_analysis()
        move_decision = StrategyDecision(
            action=StrategyAction.MOVE_TOPIC,
            target_day=22,
            target_objective=None,
            difficulty=DifficultyLevel.MEDIUM,
            intent="probe_new_topic",
            reasoning="Moving on",
            follow_up=False,
            should_end=False,
        )
        next_q = _mock_generated_question(
            question_id="q-cov-2",
            question="What are vector databases?",
            target_day=22,
            target_objective="day-22-obj-0",
        )

        orch, _, _, _, _ = _build_orchestrator(
            session,
            analyzer_return=analysis,
            strategy_return=move_decision,
            qgen_return=next_q,
        )

        orch.process_answer("S1", "RAG explained")

        assert 21 in state.covered_days
        assert state.current_topic_day == 22

    def test_follow_up_does_not_mark_covered(self):
        """When strategy returns FOLLOW_UP on same day, covered_days is NOT updated."""
        session = _make_session()
        state = session["interview_state"]
        state.current_question = "Explain RAG."
        state.current_question_meta = {
            "question_id": "q-nocov",
            "target_day": 21,
            "target_objective": "day-21-obj-0",
            "difficulty": "MEDIUM",
            "intent": "probe",
        }
        state.current_topic_day = 21
        state.question_count = 1

        analysis = _mock_analysis()
        follow_decision = StrategyDecision(
            action=StrategyAction.FOLLOW_UP,
            target_day=21,
            target_objective="day-21-obj-0",
            difficulty=DifficultyLevel.MEDIUM,
            intent="follow",
            reasoning="",
            follow_up=True,
            should_end=False,
        )
        next_q = _mock_generated_question(question_id="q-nocov-2")

        orch, _, _, _, _ = _build_orchestrator(
            session,
            analyzer_return=analysis,
            strategy_return=follow_decision,
            qgen_return=next_q,
        )

        orch.process_answer("S1", "Some answer")

        assert 21 not in state.covered_days


# ======================================================================
# Test: No Current Question
# ======================================================================

class TestNoCurrentQuestion:
    def test_missing_current_question_raises(self):
        """If no current question is set, process_answer raises OrchestratorError."""
        session = _make_session()
        state = session["interview_state"]
        state.current_question = None  # No question set

        orch, _, _, _, _ = _build_orchestrator(session)

        with pytest.raises(OrchestratorError, match="No current question"):
            orch.process_answer("S1", "My answer")


# ======================================================================
# Test: InterviewShouldEnd from QuestionGenerator
# ======================================================================

class TestInterviewShouldEndException:
    def test_qgen_raises_interview_should_end(self):
        """If QuestionGenerator raises InterviewShouldEnd, interview completes gracefully."""
        session = _make_session()
        state = session["interview_state"]
        state.current_question = "Explain RAG."
        state.current_question_meta = {
            "question_id": "q-ise",
            "target_day": 21,
            "target_objective": "day-21-obj-0",
            "difficulty": "MEDIUM",
            "intent": "probe",
        }
        state.current_topic_day = 21
        state.question_count = 1

        analysis = _mock_analysis()
        continue_decision = StrategyDecision(
            action=StrategyAction.FOLLOW_UP,
            target_day=21,
            target_objective="day-21-obj-0",
            difficulty=DifficultyLevel.MEDIUM,
            intent="follow",
            reasoning="",
            follow_up=True,
            should_end=False,
        )

        orch, _, _, _, mock_qgen = _build_orchestrator(
            session,
            analyzer_return=analysis,
            strategy_return=continue_decision,
        )
        mock_qgen.generate.side_effect = InterviewShouldEnd("Interview should end")

        response = orch.process_answer("S1", "My answer")

        assert response.done is True
        assert state.done is True
        assert state.interview_completed is True
