"""
Interview Loop Orchestrator.

Coordinates existing services into a complete interview loop:

    SessionManager → InterviewPlan → QuestionGenerator → first question
    Candidate Answer → AnswerAnalyzer → SessionManager → StrategyEngine → QuestionGenerator → next question

Responsibilities:
    - Coordinate service calls in the correct sequence.
    - Manage question metadata traceability (question_id, objective_id).
    - Enforce question budget.
    - Translate service errors into OrchestratorError for the API layer.

Does NOT:
    - Mutate KnowledgeModel or EvidenceLedger directly (delegates to SessionManager).
    - Call Breeth directly (delegates to AnswerAnalyzer.analyze_with_memory).
    - Make strategic decisions (delegates to StrategyEngine).
    - Generate questions (delegates to QuestionGenerator).
"""
from typing import Optional, List, Dict, Any

from models.interview import (
    InterviewResponse,
    InterviewState,
    InterviewPlan,
    CandidateKnowledgeModel,
    EvidenceLedger,
    CandidateEvidenceAnalysis,
    CandidateTopicKnowledge,
    ObjectiveKnowledge,
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
from services.session_manager import session_manager as default_session_manager, SessionManager
from services.answer_analyzer import AnswerAnalyzer
from services.strategy_engine import StrategyEngine
from services.question_generator import QuestionGenerator


class OrchestratorError(Exception):
    """Raised when the orchestration layer encounters an unrecoverable error."""
    pass


class InterviewOrchestrator:
    """
    Thin orchestration layer coordinating existing interview services.

    All services are dependency-injected for testability.
    """

    def __init__(
        self,
        session_mgr: Optional[SessionManager] = None,
        analyzer: Optional[AnswerAnalyzer] = None,
        strategy: Optional[StrategyEngine] = None,
        qgen: Optional[QuestionGenerator] = None,
    ):
        self.session_manager = session_mgr or default_session_manager
        self.answer_analyzer = analyzer or AnswerAnalyzer()
        self.strategy_engine = strategy or StrategyEngine()
        self.question_generator = qgen or QuestionGenerator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_interview(self, session_id: str) -> InterviewResponse:
        """
        Generate and return the first interview question for a newly created session.

        The session must already exist (created by SessionManager.create_session).
        """
        session = self._get_session_or_raise(session_id)
        interview_state: InterviewState = session["interview_state"]
        plan: Optional[InterviewPlan] = interview_state.interview_plan

        if plan is None or not plan.topic_plans:
            raise OrchestratorError(
                "Cannot start interview: no interview plan or topic plans available."
            )

        # Build the initial StrategyDecision directly from the plan.
        # There is no prior evidence, so StrategyEngine (which requires latest_analysis)
        # is not called.  Instead, we construct a MOVE_TOPIC decision targeting the
        # first planned day and its first objective.
        first_topic = plan.topic_plans[0]
        knowledge_model: CandidateKnowledgeModel = session["knowledge_model"]
        first_objective_id = self._first_objective_id(first_topic.day, knowledge_model)

        initial_decision = StrategyDecision(
            action=StrategyAction.MOVE_TOPIC,
            target_day=first_topic.day,
            target_objective=first_objective_id,
            difficulty=DifficultyLevel.MEDIUM,
            intent="initial_topic_probe",
            reasoning="Starting interview with the first planned curriculum topic.",
            follow_up=False,
            should_end=False,
        )

        # Generate the first question
        generated = self._generate_question(
            decision=initial_decision,
            session=session,
        )

        # Store question state
        self._store_generated_question(session, generated)

        # Record the interviewer question in conversation history
        self.session_manager.add_message(session_id, "assistant", generated.question)

        return InterviewResponse(reply=generated.question, done=False)

    def process_answer(
        self, session_id: str, candidate_answer: str
    ) -> InterviewResponse:
        """
        Process a candidate answer through the full interview pipeline:

        1. Capture current question metadata.
        2. Record candidate answer in conversation.
        3. AnswerAnalyzer.analyze_with_memory() — Breeth retrieval + analysis + Breeth storage.
        4. SessionManager.apply_evidence_analysis() — state mutation.
        5. StrategyEngine.decide() — next action.
        6. If END → complete interview.
        7. Else → QuestionGenerator → next question.
        """
        session = self._get_session_or_raise(session_id)
        interview_state: InterviewState = session["interview_state"]

        # Guard: already completed
        if interview_state.done or interview_state.interview_completed:
            raise OrchestratorError("Interview already completed.")

        # Guard: no current question to answer
        if not interview_state.current_question:
            raise OrchestratorError("No current question to answer.")

        # ------------------------------------------------------------------
        # Step 1: Capture current question metadata BEFORE any mutation
        # ------------------------------------------------------------------
        meta = interview_state.current_question_meta or {}
        current_question_text = interview_state.current_question
        question_id = meta.get("question_id", "")
        target_day = meta.get("target_day")
        target_objective = meta.get("target_objective")
        turn_number = interview_state.question_count  # Nth question being answered

        # ------------------------------------------------------------------
        # Step 2: Record candidate answer (increments current_turn via add_message)
        # ------------------------------------------------------------------
        self.session_manager.add_message(session_id, "user", candidate_answer)

        # ------------------------------------------------------------------
        # Step 3: Answer Analysis (Breeth retrieval + LLM analysis + Breeth storage)
        # ------------------------------------------------------------------
        plan: InterviewPlan = interview_state.interview_plan
        knowledge_model: CandidateKnowledgeModel = session["knowledge_model"]

        # Determine topic title and objectives for the analyzer
        topic_title = self._topic_title_for_day(target_day, knowledge_model, plan)
        objectives_text = self._objectives_text_for_day(target_day, plan)
        topic_knowledge = self._topic_knowledge_for_day(target_day, knowledge_model)

        analyzer_input = AnswerAnalyzerInput(
            candidate_id=interview_state.candidate_id,
            current_question=current_question_text,
            candidate_answer=candidate_answer,
            curriculum_day=target_day,
            topic=topic_title,
            relevant_objectives=objectives_text,
            current_topic_knowledge=topic_knowledge,
            conversation_history=list(interview_state.conversation),
            relevant_memories=[],  # analyze_with_memory fills this from Breeth
        )

        try:
            analysis: CandidateEvidenceAnalysis = (
                self.answer_analyzer.analyze_with_memory(
                    session_id=session_id,
                    input_data=analyzer_input,
                    turn_number=turn_number,
                    store_turn=True,
                )
            )
        except AnalyzerError as e:
            raise OrchestratorError(f"Answer analysis failed: {e}")

        # Store latest analysis in the session dict for diagnostic endpoints
        session["latest_analysis"] = analysis

        # ------------------------------------------------------------------
        # Step 4: State mutation via SessionManager
        # ------------------------------------------------------------------
        self.session_manager.apply_evidence_analysis(
            session_id=session_id,
            analysis=analysis,
            question_id=question_id,
            objective_id=target_objective,
        )

        # Mark question as completed
        if question_id:
            interview_state.completed_question_ids.append(question_id)

        # ------------------------------------------------------------------
        # Step 5: Check question budget BEFORE strategy
        # ------------------------------------------------------------------
        if (
            plan
            and interview_state.question_count >= plan.total_question_budget
        ):
            interview_state.done = True
            interview_state.interview_completed = True
            return InterviewResponse(
                reply="Thank you for completing the interview. Your responses have been recorded.",
                done=True,
            )

        # ------------------------------------------------------------------
        # Step 6: Strategy decision on UPDATED state
        # ------------------------------------------------------------------
        evidence_ledger: EvidenceLedger = session["evidence_ledger"]

        strategy_input = StrategyEngineInput(
            interview_state=interview_state,
            interview_plan=plan,
            knowledge_model=knowledge_model,
            evidence_ledger=evidence_ledger,
            latest_analysis=analysis,
            relevant_memories=[],
        )

        try:
            decision: StrategyDecision = self.strategy_engine.decide(strategy_input)
        except Exception as e:
            raise OrchestratorError(f"Strategy decision failed: {e}")

        # ------------------------------------------------------------------
        # Step 7: Handle END
        # ------------------------------------------------------------------
        if decision.should_end:
            interview_state.done = True
            interview_state.interview_completed = True
            return InterviewResponse(
                reply="Thank you for completing the interview. Your responses have been recorded.",
                done=True,
            )

        # ------------------------------------------------------------------
        # Step 8: Generate next question
        # ------------------------------------------------------------------
        try:
            generated = self._generate_question(decision=decision, session=session)
        except InterviewShouldEnd:
            # QuestionGenerator raised InterviewShouldEnd — honour it
            interview_state.done = True
            interview_state.interview_completed = True
            return InterviewResponse(
                reply="Thank you for completing the interview. Your responses have been recorded.",
                done=True,
            )

        # Update covered_days: only when StrategyEngine explicitly issues MOVE_TOPIC
        # and we're leaving a previous day that had questions asked on it.
        if (
            decision.action == StrategyAction.MOVE_TOPIC
            and interview_state.current_topic_day is not None
            and interview_state.current_topic_day not in interview_state.covered_days
        ):
            interview_state.covered_days.append(interview_state.current_topic_day)

        # Store the new question
        self._store_generated_question(session, generated)

        # Record interviewer question in conversation
        self.session_manager.add_message(session_id, "assistant", generated.question)

        return InterviewResponse(reply=generated.question, done=False)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_session_or_raise(self, session_id: str) -> Dict[str, Any]:
        session = self.session_manager.get_session(session_id)
        if session is None:
            raise OrchestratorError(f"Session '{session_id}' not found.")
        return session

    def _first_objective_id(
        self, day: int, knowledge_model: CandidateKnowledgeModel
    ) -> Optional[str]:
        """Return the first UNKNOWN objective ID for a given day, or None."""
        topic_k = knowledge_model.topics.get(day)
        if topic_k:
            for obj_id, obj_k in topic_k.objectives.items():
                if obj_k.understanding_level == "UNKNOWN":
                    return obj_id
        return None

    def _topic_title_for_day(
        self,
        day: Optional[int],
        knowledge_model: CandidateKnowledgeModel,
        plan: Optional[InterviewPlan],
    ) -> str:
        """Resolve topic title for a curriculum day."""
        if day is not None:
            topic_k = knowledge_model.topics.get(day)
            if topic_k:
                return topic_k.topic
            if plan:
                for tp in plan.topic_plans:
                    if tp.day == day:
                        return tp.title
        return "General"

    def _objectives_text_for_day(
        self, day: Optional[int], plan: Optional[InterviewPlan]
    ) -> List[str]:
        """Return the objective TEXT strings for a day from the interview plan."""
        if day is not None and plan:
            for tp in plan.topic_plans:
                if tp.day == day:
                    return tp.objectives
        return []

    def _topic_knowledge_for_day(
        self, day: Optional[int], knowledge_model: CandidateKnowledgeModel
    ) -> CandidateTopicKnowledge:
        """Return the CandidateTopicKnowledge for a day, or a default UNKNOWN stub."""
        if day is not None:
            topic_k = knowledge_model.topics.get(day)
            if topic_k:
                return topic_k
        return CandidateTopicKnowledge(
            curriculum_day=day or 0,
            topic="Unknown",
        )

    def _generate_question(
        self, decision: StrategyDecision, session: Dict[str, Any]
    ) -> GeneratedQuestion:
        """Build QuestionGeneratorInput and call QuestionGenerator.generate()."""
        interview_state: InterviewState = session["interview_state"]
        plan: InterviewPlan = interview_state.interview_plan
        knowledge_model: CandidateKnowledgeModel = session["knowledge_model"]
        evidence_ledger: EvidenceLedger = session["evidence_ledger"]

        # Gather recent evidence (last 3 items)
        recent_evidence = evidence_ledger.items[-3:] if evidence_ledger.items else []

        # Gather recent conversation (last 4 messages)
        recent_conversation = list(interview_state.conversation[-4:])

        qg_input = QuestionGeneratorInput(
            candidate_id=interview_state.candidate_id,
            strategy_decision=decision,
            interview_state=interview_state,
            interview_plan=plan,
            knowledge_model=knowledge_model,
            evidence_ledger=evidence_ledger,
            recent_evidence=recent_evidence,
            recent_conversation=recent_conversation,
            relevant_memories=[],
        )

        try:
            return self.question_generator.generate(qg_input)
        except InterviewShouldEnd:
            raise  # Let caller handle this
        except QuestionGeneratorError as e:
            raise OrchestratorError(f"Question generation failed: {e}")

    def _store_generated_question(
        self, session: Dict[str, Any], generated: GeneratedQuestion
    ) -> None:
        """Persist question text and structured metadata into InterviewState."""
        interview_state: InterviewState = session["interview_state"]

        interview_state.current_question = generated.question
        interview_state.current_question_meta = {
            "question_id": generated.question_id,
            "target_day": generated.target_day,
            "target_objective": generated.target_objective,
            "difficulty": generated.difficulty.value if generated.difficulty else None,
            "intent": generated.intent,
        }
        interview_state.current_topic_day = generated.target_day
        interview_state.question_count += 1


# Global default instance
interview_orchestrator = InterviewOrchestrator()
