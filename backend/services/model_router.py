import os
import time
from typing import Optional, Set
from models.interview import LLMResponse
from services.groq_client import groq_client, GroqClient

RETRYABLE_ERROR_CATEGORIES: Set[str] = {
    "rate limit",
    "timeout",
    "connection error",
    "provider error",
}


class ModelRouter:
    """
    Model routing and automatic failover layer.
    
    Routes generation requests to the primary model first (LLM_PRIMARY_MODEL).
    If a retryable error occurs (rate limit, timeout, connection error, provider error),
    automatically fails over to the fallback model (LLM_FALLBACK_MODEL) if configured.
    
    Non-retryable errors (authentication error, invalid request) will NOT trigger a fallback attempt.
    """

    def __init__(
        self,
        client: Optional[GroqClient] = None,
        primary_model: Optional[str] = None,
        fallback_model: Optional[str] = None,
    ) -> None:
        self._client = client or groq_client
        self._primary_model = primary_model
        self._fallback_model = fallback_model

    @property
    def primary_model(self) -> str:
        """Return configured primary model name."""
        if self._primary_model is not None:
            return self._primary_model
        return os.getenv("LLM_PRIMARY_MODEL", "openai/gpt-oss-120b")

    @property
    def fallback_model(self) -> Optional[str]:
        """Return configured fallback model name, if set."""
        if self._fallback_model is not None:
            return self._fallback_model.strip() or None
        val = os.getenv("LLM_FALLBACK_MODEL", "").strip()
        return val if val else None

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model_override: Optional[str] = None,
        temperature: float = 0.7,
        timeout: float = 15.0,
    ) -> LLMResponse:
        """
        Generate an LLM completion with automatic failover support.
        
        Strategy:
        1. Attempt completion using primary model (or model_override).
        2. If primary succeeds, return LLMResponse.
        3. If primary fails with a retryable error AND fallback_model is configured,
           attempt completion using fallback_model.
        4. Return normalized LLMResponse.
        """
        target_primary = model_override or self.primary_model
        start_time = time.perf_counter()

        # --- Attempt 1: Primary Model ---
        res1 = self._client.generate_chat_completion(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model_override=target_primary,
            timeout=timeout,
        )

        latency1 = round((time.perf_counter() - start_time) * 1000, 2)

        if res1.get("success"):
            return LLMResponse(
                content=res1.get("response_text", ""),
                model_used=res1.get("model", target_primary),
                provider="groq",
                latency_ms=latency1,
                success=True,
                error_category=None,
            )

        # Primary failed. Check error category and fallback configuration.
        error_cat1 = res1.get("error_category") or "unknown error"
        target_fallback = self.fallback_model

        # Only attempt fallback if error is retryable AND a fallback model is set and different
        if error_cat1 in RETRYABLE_ERROR_CATEGORIES and target_fallback and target_fallback != target_primary:
            # --- Attempt 2: Fallback Model ---
            res2 = self._client.generate_chat_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model_override=target_fallback,
                timeout=timeout,
            )

            latency2 = round((time.perf_counter() - start_time) * 1000, 2)

            if res2.get("success"):
                return LLMResponse(
                    content=res2.get("response_text", ""),
                    model_used=res2.get("model", target_fallback),
                    provider="groq",
                    latency_ms=latency2,
                    success=True,
                    error_category=None,
                )

            # Fallback also failed
            error_cat2 = res2.get("error_category") or error_cat1
            return LLMResponse(
                content="",
                model_used=target_fallback,
                provider="groq",
                latency_ms=latency2,
                success=False,
                error_category=error_cat2,
            )

        # Non-retryable error or no fallback configured
        return LLMResponse(
            content="",
            model_used=target_primary,
            provider="groq",
            latency_ms=latency1,
            success=False,
            error_category=error_cat1,
        )


# Default global instance
model_router = ModelRouter()
