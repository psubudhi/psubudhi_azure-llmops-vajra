from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Any

import httpx
import pandas as pd


class PredictionAPIError(RuntimeError):
    pass


@dataclass
class _FeatureFrameProxy:
    client: "PredictionAPIClient"

    def __len__(self) -> int:
        return int(self.client.model_info()["row_count"])


class PredictionAPIClient:
    """Compatibility facade matching the subset of MLModelService used by app.py."""

    def __init__(self, base_url: str | None = None, timeout_seconds: float | None = None) -> None:
        self.base_url = (base_url or os.getenv("VAJRA_PREDICTION_API_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.timeout_seconds = timeout_seconds or float(os.getenv("VAJRA_UI_API_TIMEOUT_SECONDS", "90"))
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds)
        self.features_df = _FeatureFrameProxy(self)
        self._model_info_cache: dict[str, Any] | None = None

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = self._client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text
            raise PredictionAPIError(
                f"Prediction API returned {exc.response.status_code} for {path}: {detail}"
            ) from exc
        except httpx.HTTPError as exc:
            raise PredictionAPIError(
                f"Cannot reach Prediction API at {self.base_url}. Start it with: "
                "uvicorn services.prediction_api.app.main:app --host 0.0.0.0 --port 8000"
            ) from exc

    def ensure_loaded(self) -> None:
        self._request("GET", "/health/ready")

    def model_info(self, refresh: bool = False) -> dict[str, Any]:
        if refresh or self._model_info_cache is None:
            self._model_info_cache = self._request("GET", "/api/v1/model/info")
        return self._model_info_cache

    def predict_condition(self, row_index: int | None = None, strategy: str = "latest") -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v1/predictions",
            json={"row_index": row_index, "strategy": strategy},
        )

    def row_by_index(self, row_index: int | None = None, strategy: str = "latest") -> pd.Series:
        if row_index is None:
            prediction = self.predict_condition(strategy=strategy)
            row_index = int(prediction["row_index"])
        row = self._request("GET", f"/api/v1/rows/{int(row_index)}")
        return pd.Series(row)

    def set_demo_override(
        self,
        row_index: int,
        row: pd.Series | dict[str, Any],
        meta: dict[str, Any] | None = None,
    ) -> None:
        row_dict = row.to_dict() if isinstance(row, pd.Series) else dict(row)
        row_dict = _json_safe(row_dict)
        self._request(
            "POST",
            "/api/v1/demo/apply",
            json={"row_index": int(row_index), "row": row_dict, "meta": dict(meta or {})},
        )

    def clear_demo_override(self) -> None:
        self._request("POST", "/api/v1/demo/clear")

    def get_demo_override(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/demo")

    def plant_topology(self, row_index: int | None = None, strategy: str = "latest") -> list[dict[str, Any]]:
        params: dict[str, Any] = {"strategy": strategy}
        if row_index is not None:
            params["row_index"] = int(row_index)
        return self._request("GET", "/api/v1/topology", params=params)

    def active_alarms(self, top_n: int = 20) -> pd.DataFrame:
        rows = self._request("GET", "/api/v1/alarms/active", params={"top_n": top_n})
        return pd.DataFrame(rows)

    def alarm_events(self, top_n: int = 25, min_risk: str = "high", gap: int = 8) -> pd.DataFrame:
        rows = self._request(
            "GET",
            "/api/v1/alarms/events",
            params={"top_n": top_n, "min_risk": min_risk, "gap": gap},
        )
        return pd.DataFrame(rows)

    def maintenance_queue(self, top_n: int = 8) -> pd.DataFrame:
        rows = self._request("GET", "/api/v1/maintenance/queue", params={"top_n": top_n})
        return pd.DataFrame(rows)

    def telemetry_window(
        self,
        row_index: int | None = None,
        stand: int = 3,
        window: int = 250,
    ) -> pd.DataFrame:
        params: dict[str, Any] = {"stand": stand, "window": window, "mode": "raw"}
        if row_index is not None:
            params["row_index"] = int(row_index)
        rows = self._request("GET", "/api/v1/telemetry/window", params=params)
        return pd.DataFrame(rows)

    def telemetry_window_normalized(
        self,
        row_index: int | None = None,
        stand: int = 3,
        window: int = 250,
        mode: str = "zscore",
    ) -> pd.DataFrame:
        params: dict[str, Any] = {"stand": stand, "window": window, "mode": mode}
        if row_index is not None:
            params["row_index"] = int(row_index)
        rows = self._request("GET", "/api/v1/telemetry/window", params=params)
        return pd.DataFrame(rows)

    def telemetry_groups(
        self,
        row_index: int | None = None,
        stand: int = 3,
        window: int = 250,
    ) -> dict[str, pd.DataFrame]:
        params: dict[str, Any] = {"stand": stand, "window": window}
        if row_index is not None:
            params["row_index"] = int(row_index)
        groups = self._request("GET", "/api/v1/telemetry/groups", params=params)
        return {name: pd.DataFrame(rows) for name, rows in groups.items()}

    def metrics(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/model/metrics")

    @property
    def drift_psi(self) -> pd.DataFrame:
        return pd.DataFrame(self._request("GET", "/api/v1/model/drift"))

    @property
    def feature_importance(self) -> pd.DataFrame:
        return pd.DataFrame(self._request("GET", "/api/v1/model/feature-importance"))

    @staticmethod
    def default_action_for_fault(fault: str, risk_level: str = "") -> str:
        f = str(fault).lower()
        risk = str(risk_level).lower()
        prefix = "Inspect immediately" if risk == "critical" else "Schedule focused inspection"
        if "bearing" in f:
            return f"{prefix}: verify bearing lubrication, housing temperature, vibration/noise, and coupling alignment."
        if "electric" in f:
            return f"{prefix}: check drive alarms, current imbalance, cooling, and power-to-torque behaviour."
        if "workroll" in f:
            return f"{prefix}: check emulsion/lubrication, roll surface condition, cooling nozzles, and roll mileage."
        if "reduction" in f:
            return f"{prefix}: verify reduction schedule, roll gap calibration, force distribution, and inter-stand tension."
        return f"{prefix}: review telemetry evidence, physical rules, SOP guidance, and adjacent stand impact."


prediction_api = PredictionAPIClient()


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return str(value)
