from __future__ import annotations

import json
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .config import settings


def get_llm(temperature: float = 0.1) -> ChatOpenAI:
    return ChatOpenAI(model=settings.openai_model, temperature=temperature)


def _fallback_text(system: str, user: str, exc: Exception | None = None) -> str:
    return (
        "Vajra could not call the configured LLM at this moment, so it returned a deterministic fallback.\n\n"
        "Please check OPENAI_API_KEY, OPENAI_MODEL, and internet/API access. The ML, telemetry, rules, "
        "drift, logbook, and feedback layers can still run locally.\n\n"
        f"LLM error: {type(exc).__name__ if exc else 'unknown'}"
    )


def invoke_text(system: str, user: str, temperature: float = 0.1) -> str:
    try:
        llm = get_llm(temperature=temperature)
        resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return str(resp.content)
    except Exception as exc:
        return _fallback_text(system, user, exc)


def invoke_json(system: str, user: str, temperature: float = 0.0) -> dict[str, Any]:
    try:
        llm = get_llm(temperature=temperature)
        resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        text = str(resp.content).strip()
        if text.startswith("```"):
            text = text.strip("`")
            text = text.replace("json\n", "", 1).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
        try:
            return json.loads(text)
        except Exception:
            return {"raw_text": str(resp.content)}
    except Exception as exc:
        return {"llm_error": f"{type(exc).__name__}: {exc}", "fallback": True}
