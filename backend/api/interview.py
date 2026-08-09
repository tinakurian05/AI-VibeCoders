from typing import Optional
from fastapi import APIRouter, HTTPException, status

from models.interview import (
    InterviewRequest,
    InterviewResponse,
    CandidateEvidenceAnalysis,
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
    InterviewShouldEnd,
    QuestionGeneratorError,
)
from services.session_manager import session_manager
from services.answer_analyzer import AnswerAnalyzer
from services.interview_memory import interview_memory_service
from services.strategy_engine import StrategyEngine
from services.question_generator import QuestionGenerator

router = APIRouter(prefix="/api", tags=["Interview"])

# Global engine instances
answer_analyzer = AnswerAnalyzer()
strategy_engine = StrategyEngine()
question_generator = QuestionGenerator()


def _get_topic_title(session: dict, day: int) -> str:
    """Helper to find topic title from CurriculumState or InterviewPlan."""
    curriculum = session.get("curriculum_state")
    if curriculum and hasattr(curriculum, "days") and day in curriculum.days:
        return curriculum.days[day].title
    plan = session["interview_state"].interview_plan
    if plan and plan.topic_plans:
        for tp in plan.topic_plans:
            if tp.day == day:
                return tp.title
    return f"Day {day} Topic"


@router.post("/interview", response_model=InterviewResponse)
def handle_interview(request: InterviewRequest) -> InterviewResponse:
    """
    POST /api/interview
    
    Handles interview turns maintaining state via sessionId.
    - First request: includes candidate object -> initializes session & generates initial question.
    - Subsequent requests: includes candidate's response message -> analyzes answer, updates state,
      determines strategy, generates next question, and stores completed turn in Breeth memory.
    """
    try:
        session_id = request.sessionId

        # 1. First request or session re-initialization with candidate profile
        if request.candidate is not None:
            if not session_manager.session_exists(session_id):
                session = session_manager.create_session(session_id, request.candidate)
            else:
                session = session_manager.get_session(session_id)

            interview_state = session["interview_state"]
            plan = interview_state.interview_plan

            # If initial question hasn't been generated yet for this new session
            if not interview_state.current_question:
                initial_day = plan.topic_plans[0].day if (plan and plan.topic_plans) else (plan.selected_days[0] if (plan and plan.selected_days) else 1)
                initial_obj = plan.topic_plans[0].objectives[0] if (plan and plan.topic_plans and plan.topic_plans[0].objectives) else None

                initial_decision = StrategyDecision(
                    action=StrategyAction.MOVE_TOPIC,
                    target_day=initial_day,
                    target_objective=initial_obj,
                    difficulty=DifficultyLevel.MEDIUM,
                    intent="initial_interview_question",
                    reasoning="Opening question for candidate interview.",
                    follow_up=False,
                    should_end=False,
                )

                cand_id = session["candidate_state"].candidate_id if session.get("candidate_state") else interview_state.candidate_id

                q_input = QuestionGeneratorInput(
                    candidate_id=cand_id,
                    strategy_decision=initial_decision,
                    interview_state=interview_state,
                    interview_plan=plan,
                    knowledge_model=session["knowledge_model"],
                    evidence_ledger=session["evidence_ledger"],
                    latest_analysis=None,
                    recent_evidence=[],
                    recent_conversation=[],
                    relevant_memories=[],
                )

                try:
                    first_q = question_generator.generate(q_input)
                    question_text = first_q.question
                    interview_state.current_topic_day = first_q.target_day
                except Exception:
                    # Fallback initial question if LLM generation fails or is offline
                    topic_title = _get_topic_title(session, initial_day)
                    question_text = f"Welcome! To start off our technical conversation on {topic_title}, could you give an overview of your experience with it?"
                    interview_state.current_topic_day = initial_day

                interview_state.current_question = question_text
                session_manager.add_message(session_id, "assistant", question_text)

                return InterviewResponse(
                    reply=question_text,
                    done=False,
                    feedback=None,
                )

            # If session already had a current question generated
            return InterviewResponse(
                reply=interview_state.current_question,
                done=False,
                feedback=None,
            )

        # 2. Subsequent turn request with candidate answer message
        elif request.message is not None:
            session = session_manager.get_session(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session '{session_id}' not found."
                )

            interview_state = session["interview_state"]

            # Check if interview is already completed
            if interview_state.interview_completed or interview_state.done:
                return InterviewResponse(
                    reply="The interview has concluded. Thank you!",
                    done=True,
                    feedback=None,
                )

            # Store user message in conversation history
            session_manager.add_message(session_id, "user", request.message)

            # Identify current context
            plan = interview_state.interview_plan
            current_day = interview_state.current_topic_day or (plan.topic_plans[0].day if (plan and plan.topic_plans) else (plan.selected_days[0] if (plan and plan.selected_days) else 1))
            current_question = interview_state.current_question or f"Question on Day {current_day}"
            topic_title = _get_topic_title(session, current_day)

            # 2a. Retrieve relevant Breeth memories (fails gracefully to [])
            memories = interview_memory_service.get_relevant_memories(
                session_id=session_id,
                query=topic_title,
                limit=5,
            )

            # 2b. Run Answer Analysis using AnswerAnalyzer.analyze_with_memory()
            try:
                analysis = answer_analyzer.analyze_with_memory(
                    session_id=session_id,
                    topic=topic_title,
                    current_question=current_question,
                    candidate_answer=request.message,
                    curriculum_day=current_day,
                )
            except Exception:
                # Fallback analysis on unexpected failure
                analysis = CandidateEvidenceAnalysis(
                    curriculum_day=current_day,
                    topic=topic_title,
                    understanding_assessment="MEDIUM",
                    assessment_type="supports_understanding",
                    confidence=0.5,
                    strengths=["Answer received"],
                    gaps=[],
                    evidence_text=request.message[:200],
                    candidate_claim=request.message[:100],
                    follow_up_recommended=False,
                )

            # 2c. Apply evidence analysis via SessionManager (no direct LLM state mutation)
            turn_num = interview_state.question_count + 1
            q_id = f"q-{turn_num}"
            session_manager.apply_evidence_analysis(session_id, analysis, question_id=q_id)

            # Update live interview state progress
            interview_state.question_count += 1
            if current_day not in interview_state.covered_days:
                interview_state.covered_days.append(current_day)

            # 2d. Invoke StrategyEngine
            strategy_input = StrategyEngineInput(
                interview_state=interview_state,
                interview_plan=plan,
                knowledge_model=session["knowledge_model"],
                evidence_ledger=session["evidence_ledger"],
                latest_analysis=analysis,
                relevant_memories=memories,
            )
            decision = strategy_engine.decide(strategy_input)

            # Check if strategy indicates ending the interview
            if decision.should_end or decision.action == StrategyAction.END:
                interview_state.interview_completed = True
                interview_state.done = True

                # Store final completed turn in Breeth safely
                interview_memory_service.store_turn(
                    session_id=session_id,
                    turn_number=interview_state.question_count,
                    question=current_question,
                    candidate_answer=request.message,
                    curriculum_day=current_day,
                    topic=topic_title,
                    analysis=analysis,
                )

                closing_msg = "Thank you for completing the interview. Your responses have been recorded."
                session_manager.add_message(session_id, "assistant", closing_msg)
                return InterviewResponse(
                    reply=closing_msg,
                    done=True,
                    feedback=None,
                )

            # 2e. Invoke QuestionGenerator for next question
            recent_ev = session["evidence_ledger"].get_evidence_for_day(current_day)
            recent_conv = session.get("conversation_history", [])[-4:]

            cand_id = session["candidate_state"].candidate_id if session.get("candidate_state") else interview_state.candidate_id

            q_input = QuestionGeneratorInput(
                candidate_id=cand_id,
                strategy_decision=decision,
                interview_state=interview_state,
                interview_plan=plan,
                knowledge_model=session["knowledge_model"],
                evidence_ledger=session["evidence_ledger"],
                latest_analysis=analysis,
                recent_evidence=recent_ev,
                recent_conversation=recent_conv,
                relevant_memories=memories,
            )

            try:
                next_q = question_generator.generate(q_input)
                next_question_text = next_q.question
                interview_state.current_topic_day = next_q.target_day
            except InterviewShouldEnd:
                interview_state.interview_completed = True
                interview_state.done = True
                closing_msg = "Thank you for completing the interview."
                session_manager.add_message(session_id, "assistant", closing_msg)
                return InterviewResponse(
                    reply=closing_msg,
                    done=True,
                    feedback=None,
                )
            except Exception:
                # Fallback question if generator fails
                next_day = decision.target_day
                next_topic = _get_topic_title(session, next_day)
                next_question_text = f"Building on that, could you share your thoughts on {next_topic}?"
                interview_state.current_topic_day = next_day

            interview_state.current_question = next_question_text

            # 2f. Store completed turn in Breeth safely (fails gracefully)
            interview_memory_service.store_turn(
                session_id=session_id,
                turn_number=interview_state.question_count,
                question=current_question,
                candidate_answer=request.message,
                curriculum_day=current_day,
                topic=topic_title,
                analysis=analysis,
            )

            # Store next question in conversation history
            session_manager.add_message(session_id, "assistant", next_question_text)

            return InterviewResponse(
                reply=next_question_text,
                done=False,
                feedback=None,
            )

        # 3. Payload missing both candidate and message
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request payload must contain either 'candidate' or 'message'."
            )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}"
        )
