from fastapi import APIRouter, HTTPException, status
from models.interview import InterviewRequest, InterviewResponse
from services.session_manager import session_manager

router = APIRouter(prefix="/api", tags=["Interview"])


@router.post("/interview", response_model=InterviewResponse)
def handle_interview(request: InterviewRequest) -> InterviewResponse:
    """
    POST /api/interview
    
    Handles interview turns maintaining state via sessionId.
    - First request: includes candidate object -> initializes session.
    - Subsequent requests: includes candidate's response message -> updates session.
    """
    try:
        session_id = request.sessionId

        # 1. New session or re-initialization request with candidate object
        if request.candidate is not None:
            if not session_manager.session_exists(session_id):
                session_manager.create_session(session_id, request.candidate)
            
            return InterviewResponse(
                reply="Welcome. Let's begin your interview.",
                done=False
            )

        # 2. Subsequent turn request with candidate message
        elif request.message is not None:
            session = session_manager.get_session(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session '{session_id}' not found."
                )

            # Store the message in conversation history
            session_manager.add_message(session_id, "user", request.message)

            return InterviewResponse(
                reply="Response received. Interview processing will be implemented in the next step.",
                done=False
            )

        # 3. Payload missing both candidate and message
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request payload must contain either 'candidate' or 'message'."
            )

    except HTTPException:
        # Re-raise explicit HTTP exceptions
        raise
    except Exception as e:
        # Catch internal unexpected exceptions and mask detailed tracebacks
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while processing the interview request."
        )
