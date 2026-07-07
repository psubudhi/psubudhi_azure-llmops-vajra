from __future__ import annotations

import os

import httpx


def check_llm_health() -> dict:
    base_url = os.getenv(
        "VAJRA_LLM_BASE_URL",
        "http://vajra-llm-predictor.inference.svc.cluster.local/v1",
    ).rstrip("/")
    model = os.getenv("VAJRA_LLM_MODEL", "vajra-llama")

    try:
        response = httpx.get(f"{base_url}/models", timeout=10.0)
        response.raise_for_status()
        return {
            "ready": True,
            "provider": "vllm",
            "model": model,
            "base_url": base_url,
        }
    except Exception as exc:
        return {
            "ready": False,
            "provider": "vllm",
            "model": model,
            "base_url": base_url,
            "error": str(exc),
        }