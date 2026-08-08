import os
from typing import Dict, Any, List, Optional
import httpx


class MemoryService:
    """
    Service encapsulating direct HTTP interactions with the Breeth REST API
    for storing and searching interview session memories.
    
    Configuration (via environment variables):
    - BREETH_API_KEY: Authorization bearer token for Breeth API.
    - BREETH_BASE_URL: Base URL for Breeth endpoints (defaults to https://api.thebreeth.com).
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self._api_key = api_key
        self._base_url = base_url

    @property
    def api_key(self) -> Optional[str]:
        if self._api_key is not None:
            return self._api_key
        return os.getenv("BREETH_API_KEY")

    @property
    def base_url(self) -> str:
        if self._base_url is not None:
            raw_url = self._base_url
        else:
            raw_url = os.getenv("BREETH_BASE_URL", "https://api.thebreeth.com")
        return raw_url.rstrip("/")

    def is_configured(self) -> bool:
        """Return True if BREETH_API_KEY is configured and non-empty."""
        key = self.api_key
        return bool(key and key.strip())

    def _get_headers(self) -> Dict[str, str]:
        """Construct request headers. Raises ValueError if API key is missing."""
        key = self.api_key
        if not key or not key.strip():
            raise ValueError("BREETH_API_KEY is not configured in environment variables.")
        return {
            "Authorization": f"Bearer {key.strip()}",
            "Content-Type": "application/json",
        }

    def _sanitize_error(self, err: Exception) -> str:
        """Format an exception string while strictly masking any secret API key."""
        err_msg = str(err)
        key = self.api_key
        if key and key in err_msg:
            err_msg = err_msg.replace(key, "[REDACTED_API_KEY]")
        return err_msg

    def store_episode(
        self,
        session_id: str,
        messages: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """
        Store an interview memory episode via POST /v1/episodes.
        Scoped by group_id: interview:{session_id}.
        
        Returns response JSON dictionary on success, or structured fallback dictionary on failure.
        """
        if not self.is_configured():
            return {
                "success": False,
                "status": "error",
                "message": "Breeth API key is not configured."
            }

        endpoint = f"{self.base_url}/v1/episodes"
        group_id = f"interview:{session_id}"

        # Construct top-level content string required by Breeth API contract
        content_lines = []
        for msg in messages:
            if isinstance(msg, dict):
                role = str(msg.get("role", "speaker")).title()
                text = str(msg.get("content", ""))
                content_lines.append(f"{role}: {text}")
            else:
                content_lines.append(str(msg))
        content_text = "\n".join(content_lines) if content_lines else "Interview Episode"

        payload = {
            "group_id": group_id,
            "content": content_text,
            "messages": messages,
            "metadata": metadata or {}
        }

        try:
            headers = self._get_headers()
            response = httpx.post(endpoint, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                data["success"] = True
                return data
            return {"success": True, "data": data}

        except httpx.HTTPStatusError as exc:
            sanitized = self._sanitize_error(exc)
            return {
                "success": False,
                "status": "http_error",
                "status_code": exc.response.status_code,
                "message": f"HTTP status error: {exc.response.status_code}"
            }
        except httpx.TimeoutException as exc:
            return {
                "success": False,
                "status": "timeout",
                "message": "Breeth API request timed out."
            }
        except Exception as exc:
            sanitized = self._sanitize_error(exc)
            return {
                "success": False,
                "status": "error",
                "message": f"Failed to store episode: {sanitized}"
            }

    def search_memory(
        self,
        session_id: str,
        query: str,
        limit: int = 5,
        timeout: float = 10.0
    ) -> List[Dict[str, Any]]:
        """
        Search Breeth memory via POST /v1/search.
        Scoped by group_id: interview:{session_id}.
        
        Returns parsed list of memory items, or empty list [] on error/fallback.
        """
        if not self.is_configured():
            return []

        endpoint = f"{self.base_url}/v1/search"
        group_id = f"interview:{session_id}"
        payload = {
            "group_id": group_id,
            "query": query,
            "limit": limit
        }

        try:
            headers = self._get_headers()
            response = httpx.post(endpoint, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            # Normalize output into a clean internal python list representation
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                if "results" in data and isinstance(data["results"], list):
                    return data["results"]
                elif "memories" in data and isinstance(data["memories"], list):
                    return data["memories"]
                return [data]
            return []

        except Exception:
            # Fallback gracefully: memory search failure should not break interview flow
            return []


# Global default service instance
memory_service = MemoryService()
