from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_index: int | None = Field(default=None, ge=0)
    strategy: Literal["latest", "highest_risk"] = "latest"


class DemoOverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_index: int = Field(ge=0)
    row: dict[str, Any]
    meta: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: Literal["ok", "not_ready"]
    detail: str
    backend: str
    version: str
