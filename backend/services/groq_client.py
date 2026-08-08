import os
from typing import Dict, Any, Optional
import httpx


class GroqClient:
    """
    Minimal isolated client for testing GroqCloud OpenAI-compatible API connectivity.
    
    Configuration (via environment variables):
    - GROQ_API_KEY: GroqCloud API authorization key.
    - LLM_PRIMARY_MODEL: Default model name (defaults to 'openai/gpt-oss-120b').
    - GROQ_BASE_URL: Base URL for GroqCloud API (defaults to 'https://api.groq.com/openai/v1').
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url

    @property
    def api_key(self) -> Optional[str]:
        if self._api_key is not None:
            return self._api_key
        return os.getenv("GROQ_API_KEY")

    @property
    def model(self) -> str:
        if self._model is not None:
            return self._model
        return os.getenv("LLM_PRIMARY_MODEL", "openai/gpt-oss-120b")

    @property
    def base_url(self) -> str:
        if self._base_url is not None:
            raw_url = self._base_url
        else:
            raw_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        return raw_url.rstrip("/")

    def is_configured(self) -> bool:
        """Return True if GROQ_API_KEY is configured and non-empty."""
        key = self.api_key
        return bool(key and key.strip())

    def _get_headers(self) -> Dict[str, str]:
        """Construct request headers. Raises ValueError if API key is missing."""
        key = self.api_key
        if not key or not key.strip():
            raise ValueError("GROQ_API_KEY is not configured in environment variables.")
        return {
            "Authorization": f"Bearer {key.strip()}",
            "Content-Type": "application/json",
        }

    def _categorize_error(self, exc: Exception) -> str:
        """Categorize exception into a sanitized, safe error category string."""
        if isinstance(exc, httpx.HTTPStatusError):
            status_code = exc.response.status_code
            if status_code in (401, 403):
                return "authentication error"
            elif status_code == 429:
                return "rate limit"
            elif status_code in (400, 422):
                return "invalid request"
            elif status_code >= 500:
                return "provider error"
            return "http error"
        elif isinstance(exc, httpx.TimeoutException):
            return "timeout"
        elif isinstance(exc, (httpx.RequestError, httpx.ConnectError)):
            return "connection error"
        elif isinstance(exc, ValueError) and "GROQ_API_KEY" in str(exc):
            return "authentication error"
        return "unknown error"

    def generate_chat_completion(
        self,
        prompt: str = "Explain RAG in one sentence.",
        system_prompt: str = "You are a helpful assistant. Respond briefly.",
        model_override: Optional[str] = None,
        timeout: float = 15.0
    ) -> Dict[str, Any]:
        """
        Send a test chat completion request to GroqCloud's OpenAI-compatible endpoint.
        
        Returns a dictionary containing:
        - success: bool
        - model: str
        - response_text: str (if success)
        - error_category: str (if failure)
        - details: str (sanitized message)
        """
        target_model = model_override or self.model

        if not self.is_configured():
            return {
                "success": False,
                "model": target_model,
                "response_text": "",
                "error_category": "authentication error",
                "details": "GROQ_API_KEY is not set or empty."
            }

        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            headers = self._get_headers()
            response = httpx.post(endpoint, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            # Extract response text from OpenAI-compatible response format
            response_text = ""
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                response_text = message.get("content", "").strip()

            return {
                "success": True,
                "model": target_model,
                "response_text": response_text,
                "error_category": None,
                "details": "GroqCloud completion successful."
            }

        except Exception as exc:
            error_cat = self._categorize_error(exc)
            return {
                "success": False,
                "model": target_model,
                "response_text": "",
                "error_category": error_cat,
                "details": f"GroqCloud call failed with {error_cat}."
            }


# Default singleton client instance
groq_client = GroqClient()
