import os
from typing import Optional, Any
from models.interview import LLMResponse
from services.model_router import model_router, ModelRouter


class LLMGateway:
    """
    Application-level LLMGateway providing a provider-agnostic interface
    for LLM generation requests.
    
    Delegates calls to ModelRouter (model_router.py) for automatic primary-to-fallback
    routing and failover protection.
    
    IMPORTANT: This gateway contains generic LLM infrastructure and has NO knowledge of
    CandidateState, InterviewState, CandidateKnowledgeModel, EvidenceLedger, or Breeth.
    """

    def __init__(
        self,
        router: Optional[ModelRouter] = None,
        client: Optional[Any] = None,
        default_model: Optional[str] = None
    ) -> None:
        if router is not None:
            self._router = router
        elif client is not None or default_model is not None:
            self._router = ModelRouter(client=client, primary_model=default_model)
        else:
            self._router = model_router

    @property
    def primary_model(self) -> str:
        """Return configured primary model name."""
        return self._router.primary_model

    @property
    def fallback_model(self) -> Optional[str]:
        """Return configured fallback model name, if any."""
        return self._router.fallback_model

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        timeout: float = 15.0
    ) -> LLMResponse:
        """
        Generate an LLM response delegating model selection and failover to ModelRouter.
        """
        return self._router.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_override=model,
            temperature=temperature,
            timeout=timeout
        )


# Global default gateway instance
llm_gateway = LLMGateway()
