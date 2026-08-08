import os
import time
from typing import Optional
from models.interview import LLMResponse
from services.groq_client import groq_client, GroqClient


class LLMGateway:
    """
    Application-level LLMGateway providing a provider-agnostic interface
    for LLM generation requests.
    
    Delegates calls to the underlying GroqCloud client (groq_client.py) and returns
    a normalized LLMResponse.
    
    IMPORTANT: This gateway contains generic LLM infrastructure and has NO knowledge of
    CandidateState, InterviewState, CandidateKnowledgeModel, EvidenceLedger, or Breeth.
    """

    def __init__(self, client: Optional[GroqClient] = None, default_model: Optional[str] = None) -> None:
        self._client = client or groq_client
        self._default_model = default_model

    @property
    def primary_model(self) -> str:
        """Return configured primary model name."""
        if self._default_model is not None:
            return self._default_model
        return os.getenv("LLM_PRIMARY_MODEL", "openai/gpt-oss-120b")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        timeout: float = 15.0
    ) -> LLMResponse:
        """
        Generate an LLM response using the configured primary model (or model override).
        Delegates execution to groq_client.py and returns a normalized LLMResponse.
        """
        target_model = model or self.primary_model
        start_time = time.perf_counter()

        res = self._client.generate_chat_completion(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model_override=target_model,
            timeout=timeout
        )

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return LLMResponse(
            content=res.get("response_text", ""),
            model_used=res.get("model", target_model),
            provider="groq",
            latency_ms=latency_ms,
            success=res.get("success", False),
            error_category=res.get("error_category")
        )


# Global default gateway instance
llm_gateway = LLMGateway()
