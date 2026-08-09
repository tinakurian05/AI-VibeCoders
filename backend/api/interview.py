from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
from models.interview import InterviewRequest, InterviewResponse
from services.session_manager import session_manager
from services.interview_orchestrator import interview_orchestrator, OrchestratorError
from services.candidate_profile_service import candidate_profile_service
from services.curriculum_service import curriculum_service
from services.interview_planner import interview_planner
from models.analyzer import AnalyzerError
from models.question_generator import QuestionGeneratorError

router = APIRouter(prefix="/api", tags=["Interview"])


@router.get("/candidates")
def list_candidates() -> Dict[str, List[Dict[str, Any]]]:
    """
    GET /api/candidates

    Returns a list of all predefined candidate profiles from candidates.json,
    including their eligibility status for starting an interview based on planner constraints.
    """
    try:
        raw_candidates = candidate_profile_service.load_candidates()
        curriculum_state = curriculum_service.load_curriculum()
        result = []

        for cand in raw_candidates:
            member = cand.get("member", {})
            candidate_id = member.get("id")
            name = member.get("name", "Unknown")
            job_role = member.get("jobRole", "Unknown")
            years_experience = member.get("yearsExperience", 0)

            # Evaluate eligibility
            eligible = False
            eligibility_reason = None
            try:
                candidate_state = candidate_profile_service.build_candidate_state(cand)
                plan = interview_planner.plan_interview(candidate_state, curriculum_state)
                # Eligibility check: plan is valid if it contains topic plans and has questions allocated
                if plan and plan.topic_plans and plan.total_question_budget > 0:
                    eligible = True
                else:
                    eligible = False
                    eligibility_reason = plan.notes or "No topics selected by planner"
            except Exception as e:
                eligible = False
                eligibility_reason = str(e)

            result.append({
                "candidateId": candidate_id,
                "name": name,
                "jobRole": job_role,
                "yearsExperience": years_experience,
                "eligible": eligible,
                "eligibilityReason": eligibility_reason
            })

        return {"candidates": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load candidates: {e}"
        )


@router.post("/interview", response_model=InterviewResponse)
def handle_interview(request: InterviewRequest) -> InterviewResponse:
    """
    POST /api/interview

    Handles interview turns maintaining state via sessionId.
    - First request: can specify candidateId or candidate object -> initializes session.
    - Subsequent requests: includes candidate's response message -> processes answer.
    """
    try:
        session_id = request.sessionId

        # 1. First request or session re-initialization (Initialization path)
        if request.candidateId is not None or request.candidate is not None:
            # Determine candidate dict
            if request.candidateId is not None:
                try:
                    candidate_dict = candidate_profile_service.get_candidate(request.candidateId)
                except ValueError as e:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Candidate with ID '{request.candidateId}' not found."
                    )
            else:
                candidate_dict = request.candidate

            # Create session if not already existing
            if not session_manager.session_exists(session_id):
                session_manager.create_session(session_id, candidate_dict)

            # Validate the created session's interview plan before starting
            session = session_manager.get_session(session_id)
            if not session or not session.get("interview_state"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to initialize session state."
                )

            interview_state = session["interview_state"]
            plan = interview_state.interview_plan

            if plan is None or not plan.topic_plans or plan.total_question_budget == 0:
                # Remove the invalid session so it doesn't leave a broken session behind
                if session_manager.session_exists(session_id):
                    session_manager._sessions.pop(session_id, None)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Candidate is not eligible: unable to generate a valid interview plan."
                )

            # Start the interview and return the first question
            return interview_orchestrator.start_interview(session_id)

        # 2. Subsequent turn request with candidate message
        elif request.message is not None:
            if not session_manager.session_exists(session_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session '{session_id}' not found.",
                )

            return interview_orchestrator.process_answer(session_id, request.message)

        # 3. Payload missing both initialization and message
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request payload must contain either 'candidateId', 'candidate', or 'message'.",
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
