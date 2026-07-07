from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    """Stable prediction contract used by FastAPI, Streamlit, and Triton adapters."""

    model_config = ConfigDict(extra="forbid")

    source: Literal["replay"] = "replay"
    row_index: int | None = Field(default=None, ge=0)
    strategy: Literal["latest", "highest_risk"] = "latest"


class SecondaryFault(BaseModel):
    fault: str
    confidence: float
    stand: str


class PredictionResponse(BaseModel):
    """Required fields plus forward-compatible extras from the existing Vajra model."""

    model_config = ConfigDict(extra="allow")

    alarm_id: str
    row_index: int
    timestamp_index: int
    is_alert: bool
    anomaly_probability: float
    anomaly_threshold: float
    predicted_fault: str
    predicted_stand: str
    asset_name: str
    fault_confidence: float
    secondary_faults: list[SecondaryFault] = Field(default_factory=list)
    predicted_rul_band: str
    proxy_rul_observations: float
    proxy_rul_shifts: float
    trend_risk: float
    risk_score: float
    risk_level: str
    health_index: float
    evidence: list[str] = Field(default_factory=list)
    similar_historical_cases: list[dict[str, Any]] = Field(default_factory=list)
    disclaimer: str
