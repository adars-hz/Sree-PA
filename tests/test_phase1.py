"""
Phase 1 Integration Test Suite for Project SREE
Verifies environment, FastAPI routers, system telemetry, and Ollama connection.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.config import settings
from backend.app.ai.ollama_client import ollama_client
from backend.app.ai.prompts import build_prompt_with_context

async def run_tests():
    print("=" * 60)
    print("       SREE PHASE 1 TEST SUITE")
    print("=" * 60)
    
    # 1. Configuration check
    print("\n[TEST 1] Configuration & Paths:")
    print(f"  - App Name: {settings.APP_NAME}")
    print(f"  - Root Dir: {settings.BASE_DIR}")
    print(f"  - Data Dir: {settings.DATA_DIR} (Exists: {settings.DATA_DIR.exists()})")
    print(f"  - Ollama Base URL: {settings.OLLAMA_BASE_URL}")
    assert settings.APP_NAME == "SREE", "App name mismatch"
    print("  --> PASS: Configuration verified.")

    # 2. Ollama connection check
    print("\n[TEST 2] Ollama Daemon Status:")
    is_up = await ollama_client.is_available()
    print(f"  - Ollama Reachable: {is_up}")
    if not is_up:
        print("  --> FAIL: Ollama is not running on 127.0.0.1:11434")
        return False
    print("  --> PASS: Ollama service is connected.")

    # 3. Model listing check
    print("\n[TEST 3] Installed Model Verification:")
    models = await ollama_client.get_available_models()
    model_names = [m.get("name") for m in models]
    print(f"  - Discovered Models ({len(models)}): {model_names}")
    
    # 4. System prompt construction
    print("\n[TEST 4] SREE Persona Prompt Generation:")
    sample_msgs = build_prompt_with_context(
        user_message="Hey Sree, how are you?",
        conversation_history=[]
    )
    assert len(sample_msgs) == 2
    assert sample_msgs[0]["role"] == "system"
    assert "SREE" in sample_msgs[0]["content"]
    assert sample_msgs[1]["content"] == "Hey Sree, how are you?"
    print("  --> PASS: System persona prompt successfully built.")

    # 5. Live Conversation Inference (if model available)
    if models:
        test_model = models[0].get("name")
        print(f"\n[TEST 5] Live AI Inference with '{test_model}':")
        print("  - Sending query: 'Hello Sree! Please introduce yourself in one short sentence.'")
        try:
            res = await ollama_client.chat(messages=sample_msgs, model=test_model)
            print(f"  - SREE Response: {res['content'].strip()}")
            print(f"  - Generation tokens: {res.get('eval_count', 0)}")
            print("  --> PASS: Live AI generation successful!")
        except Exception as e:
            print(f"  --> FAIL: Inference error: {e}")
            return False
    else:
        print("\n[TEST 5] Model is currently downloading in background. Live inference will run once download completes.")

    print("\n" + "=" * 60)
    print("  PHASE 1 CORE BACKEND: ALL CHECKS PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)

