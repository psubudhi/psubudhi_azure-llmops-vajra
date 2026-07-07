from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _env_path(new_key: str, old_key: str, default: str) -> Path:
    return Path(os.getenv(new_key) or os.getenv(old_key) or default)


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("VAJRA_APP_NAME", "Vajra")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    modelling_root: Path = Path(os.getenv("TCM_MODELLING_ROOT", "./tcm_modelling"))
    docs_dir: Path = _env_path("VAJRA_DOCS_DIR", "STEELCARE_DOCS_DIR", "./docs")
    vector_dir: Path = _env_path("VAJRA_VECTOR_DIR", "STEELCARE_VECTOR_DIR", "./vector_store/faiss_index")
    memory_dir: Path = _env_path("VAJRA_MEMORY_DIR", "STEELCARE_MEMORY_DIR", "./memory")
    runtime_dir: Path = _env_path("VAJRA_RUNTIME_DIR", "STEELCARE_RUNTIME_DIR", "./data/runtime")
    sqlite_db_path: Path = _env_path("VAJRA_SQLITE_DB", "STEELCARE_SQLITE_DB", "./data/runtime/vajra_ops.sqlite")
    langgraph_memory_backend: str = os.getenv("LANGGRAPH_MEMORY_BACKEND", "memory")
    llm_provider: str = os.getenv("VAJRA_LLM_PROVIDER", "vllm")
    llm_base_url: str = os.getenv(
        "VAJRA_LLM_BASE_URL",
        "http://vajra-llm-predictor.inference.svc.cluster.local/v1",
    )
    llm_api_key: str = os.getenv("VAJRA_LLM_API_KEY", "EMPTY")
    llm_model: str = os.getenv("VAJRA_LLM_MODEL", "vajra-llama")
    llm_timeout_seconds: float = float(
        os.getenv("VAJRA_LLM_TIMEOUT_SECONDS", "240")
    )
    llm_max_retries: int = int(os.getenv("VAJRA_LLM_MAX_RETRIES", "2"))
    llm_max_tokens: int = int(os.getenv("VAJRA_LLM_MAX_TOKENS", "384"))

    @property
    def model_dir(self) -> Path:
        return self.modelling_root / "models"

    @property
    def output_dir(self) -> Path:
        return self.modelling_root / "outputs"

    @property
    def processed_dir(self) -> Path:
        return self.modelling_root / "data" / "processed"


settings = Settings()
