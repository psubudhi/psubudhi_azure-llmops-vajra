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
