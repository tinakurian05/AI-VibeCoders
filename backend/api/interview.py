from fastapi import APIRouter, HTTPException, status
from models.interview import InterviewRequest, InterviewResponse
from services.session_manager import session_manager
from services.interview_orchestrator import interview_orchestrator, OrchestratorError
from models.analyzer import AnalyzerError
from models.question_generator import QuestionGeneratorError

router = APIRouter(prefix="/api", tags=["Interview"])


@router.post("/interview", response_model=InterviewResponse)
def handle_interview(request: InterviewRequest) -> InterviewResponse:
    """
    POST /api/interview

    Handles interview turns maintaining state via sessionId.
    - First request: includes candidate object -> initializes session, generates first question.
    - Subsequent requests: includes candidate's response message -> processes answer through
      the full interview pipeline (AnswerAnalyzer → SessionManager → StrategyEngine → QuestionGenerator).
    """
    try:
        session_id = request.sessionId

        # 1. New session or re-initialization request with candidate object
        if request.candidate is not None:
            if not session_manager.session_exists(session_id):
                session_manager.create_session(session_id, request.candidate)

            # Generate and return the first interview question
            return interview_orchestrator.start_interview(session_id)

        # 2. Subsequent turn request with candidate message
        elif request.message is not None:
            if not session_manager.session_exists(session_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session '{session_id}' not found.",
                )

            return interview_orchestrator.process_answer(session_id, request.message)

        # 3. Payload missing both candidate and message
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request payload must contain either 'candidate' or 'message'.",
            )

    except HTTPException:
        # Re-raise explicit HTTP exceptions
        raise
    except OrchestratorError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        elif "already completed" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal error occurred while processing the interview.",
            )
    except (AnalyzerError, QuestionGeneratorError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the interview.",
        )
    except Exception:
        # Catch unexpected exceptions and mask details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while processing the interview request.",
        )
