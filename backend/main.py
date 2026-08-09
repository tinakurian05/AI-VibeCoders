import os
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from backend.api.interview import router as interview_router
except ModuleNotFoundError:
    from api.interview import router as interview_router

# Create FastAPI application instance
app = FastAPI(
    title="The Interview Agent Backend API",
    description="Backend foundation and API state management for The Interview Agent hackathon project.",
    version="1.0.0"
)

# Register interview API router
app.include_router(interview_router)


@app.get("/health")
def health_check():
    """
    GET /health
    Health check endpoint returning system status.
    """
    return {"status": "ok"}


@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler ensuring internal errors are caught and 
    sanitized to avoid exposing sensitive internal stack traces to the client.
    """
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
