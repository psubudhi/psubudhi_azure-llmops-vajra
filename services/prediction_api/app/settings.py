from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class APISettings:
    app_name: str = os.getenv("VAJRA_PREDICTION_API_NAME", "Vajra Prediction API")
    app_version: str = os.getenv("VAJRA_APP_VERSION", "0.1.0")
    prediction_backend: str = os.getenv("VAJRA_PREDICTION_BACKEND", "local").strip().lower()
    triton_url: str = os.getenv("VAJRA_TRITON_URL", "localhost:8000")
    triton_model_name: str = os.getenv("VAJRA_TRITON_MODEL_NAME", "vajra_predictor")
    triton_model_version: str = os.getenv("VAJRA_TRITON_MODEL_VERSION", "")
    request_timeout_seconds: float = float(os.getenv("VAJRA_PREDICTION_TIMEOUT_SECONDS", "60"))


settings = APISettings()
