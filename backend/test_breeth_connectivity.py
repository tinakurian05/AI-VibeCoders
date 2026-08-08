import os
import sys
import re
from pathlib import Path

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))


def load_env_file() -> bool:
    """Safely load environment variables from root or local .env file."""
    # 1. Try python-dotenv first if available
    try:
        from dotenv import load_dotenv
        root_env = Path(__file__).resolve().parent.parent / ".env"
        if root_env.exists():
            load_dotenv(dotenv_path=root_env, override=True)
        local_env = Path(__file__).resolve().parent / ".env"
        if local_env.exists():
            load_dotenv(dotenv_path=local_env, override=True)
        load_dotenv(override=True)
    except Exception:
        pass

    # 2. Robust manual parser fallback (handles quotes, UTF-8 BOM, CRLF)
    possible_paths = [
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent / ".env",
        Path(".env").resolve(),
    ]
    for env_path in possible_paths:
        if env_path.exists():
            try:
                content = env_path.read_text(encoding="utf-8-sig")
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        # Remove wrapping quotes if present
                        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                            v = v[1:-1].strip()
                        if k and v:
                            os.environ[k] = v
            except Exception:
                pass

    return bool(os.getenv("BREETH_API_KEY"))


def run_connectivity_test():
    load_env_file()
    
    from services.memory_service import memory_service
    
    print("--- Breeth Real Connectivity Verification ---")
    configured = memory_service.is_configured()
    print(f"API Key Configured: {'YES' if configured else 'NO'}")
    
    if not configured:
        print("Store Status: SKIPPED (BREETH_API_KEY is not set or empty in .env)")
        print("Search Status: SKIPPED (BREETH_API_KEY is not set or empty in .env)")
        print("\nResult: BREETH_API_KEY is missing. Skipping live API calls.")
        return False
        
    session_id = "breeth-connectivity-test"
    test_messages = [
        {"role": "interviewer", "content": "What is RAG in AI interview applications?"},
        {"role": "candidate", "content": "RAG retrieves external context to enhance answer generation."}
    ]
    test_metadata = {"test": True, "topic": "Connectivity Verification"}
    
    # 1. Test store_episode
    print(f"\n1. Executing store_episode() for session '{session_id}'...")
    store_res = memory_service.store_episode(
        session_id=session_id,
        messages=test_messages,
        metadata=test_metadata,
        timeout=10.0
    )
    
    store_success = store_res.get("success", False)
    print(f"Store Status: {'SUCCESS' if store_success else 'FAILURE'}")
    if not store_success:
        err_cat = store_res.get("status") or "unknown_error"
        err_msg = store_res.get("message") or "Failed to store episode"
        # Ensure API key is masked in output
        key = memory_service.api_key
        if key and key in err_msg:
            err_msg = err_msg.replace(key, "[REDACTED_API_KEY]")
        print(f"Sanitized Store Error: [{err_cat}] {err_msg}")

    # 2. Test search_memory
    print(f"\n2. Executing search_memory() for query 'RAG context'...")
    search_res = memory_service.search_memory(
        session_id=session_id,
        query="RAG context",
        limit=3,
        timeout=10.0
    )
    
    search_success = isinstance(search_res, list) and len(search_res) > 0
    print(f"Search Status: {'SUCCESS' if search_success else 'FAILURE / EMPTY'}")
    print(f"Items Returned: {len(search_res) if isinstance(search_res, list) else 0}")
    
    print("\n--- Summary ---")
    print(f"Live Breeth Connection Verified: {'YES' if (store_success and search_success) else 'NO'}")
    return store_success and search_success


if __name__ == "__main__":
    run_connectivity_test()
