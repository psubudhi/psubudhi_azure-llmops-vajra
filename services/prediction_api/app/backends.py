from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from src.agentic.ml_service import MLModelService

from .settings import settings


class PredictionBackend(ABC):
    @abstractmethod
    def predict(self, row_index: int | None = None, strategy: str = "latest") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def ready(self) -> tuple[bool, str]:
        raise NotImplementedError


class LocalPredictionBackend(PredictionBackend):
    """Uses the unchanged Vajra MLModelService in-process for baseline and parity."""

    def __init__(self) -> None:
        self.service = MLModelService()

    def ensure_loaded(self) -> MLModelService:
        self.service.ensure_loaded()
        return self.service

    def predict(self, row_index: int | None = None, strategy: str = "latest") -> dict[str, Any]:
        return self.ensure_loaded().predict_condition(row_index=row_index, strategy=strategy)

    def ready(self) -> tuple[bool, str]:
        try:
            self.ensure_loaded()
            return True, "local Vajra artifacts loaded"
        except Exception as exc:
            return False, str(exc)


class TritonPredictionBackend(PredictionBackend):
    """Calls the Triton Python backend through Triton's HTTP client."""

    def __init__(self) -> None:
        try:
            import tritonclient.http as httpclient
        except ImportError as exc:
            raise RuntimeError(
                "tritonclient is required when VAJRA_PREDICTION_BACKEND=triton"
            ) from exc
        self.httpclient = httpclient
        self.client = httpclient.InferenceServerClient(
            url=settings.triton_url,
            verbose=False,
            connection_timeout=settings.request_timeout_seconds,
            network_timeout=settings.request_timeout_seconds,
        )

    def predict(self, row_index: int | None = None, strategy: str = "latest") -> dict[str, Any]:
        payload = json.dumps({"row_index": row_index, "strategy": strategy})
        input_tensor = self.httpclient.InferInput("REQUEST_JSON", [1], "BYTES")
        input_tensor.set_data_from_numpy(np.asarray([payload], dtype=object))
        output = self.httpclient.InferRequestedOutput("RESULT_JSON")
        result = self.client.infer(
            model_name=settings.triton_model_name,
            model_version=settings.triton_model_version,
            inputs=[input_tensor],
            outputs=[output],
        )
        raw = result.as_numpy("RESULT_JSON")[0]
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        data = json.loads(str(raw))
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(data["error"])
        return data

    def ready(self) -> tuple[bool, str]:
        try:
            live = self.client.is_server_live()
            ready = self.client.is_server_ready()
            model_ready = self.client.is_model_ready(
                settings.triton_model_name,
                settings.triton_model_version,
            )
            ok = bool(live and ready and model_ready)
            return ok, f"triton live={live}, ready={ready}, model_ready={model_ready}"
        except Exception as exc:
            return False, str(exc)


def build_backend() -> PredictionBackend:
    if settings.prediction_backend == "triton":
        return TritonPredictionBackend()
    if settings.prediction_backend != "local":
        raise ValueError(
            f"Unsupported VAJRA_PREDICTION_BACKEND={settings.prediction_backend!r}; use local or triton."
        )
    return LocalPredictionBackend()


backend = build_backend()
