from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.agentic.ml_service import MLModelService

from .backends import LocalPredictionBackend, backend
from .schemas import DemoOverrideRequest, HealthResponse, PredictionRequest
from .serialization import to_jsonable
from .settings import settings

metadata_service = backend.service if isinstance(backend, LocalPredictionBackend) else MLModelService()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Versioned API boundary around the existing Vajra V2 prediction runtime.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _local_service() -> MLModelService:
    """Load replay metadata/telemetry locally even when prediction calls go through Triton."""
    metadata_service.ensure_loaded()
    return metadata_service


@app.get("/health/live", response_model=HealthResponse)
def live() -> HealthResponse:
    return HealthResponse(
        status="ok",
        detail="prediction API process is running",
        backend=settings.prediction_backend,
        version=settings.app_version,
    )


@app.get("/health/ready", response_model=HealthResponse)
def ready() -> HealthResponse:
    ok, detail = backend.ready()
    if not ok:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "detail": detail,
                "backend": settings.prediction_backend,
                "version": settings.app_version,
            },
        )
    return HealthResponse(
        status="ok",
        detail=detail,
        backend=settings.prediction_backend,
        version=settings.app_version,
    )


@app.get("/api/v1/version")
def version() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "prediction_backend": settings.prediction_backend,
    }


@app.post("/api/v1/predictions")
def create_prediction(request: PredictionRequest) -> dict[str, Any]:
    try:
        result = backend.predict(row_index=request.row_index, strategy=request.strategy)
        return to_jsonable(result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc


@app.get("/api/v1/model/info")
def model_info() -> dict[str, Any]:
    service = _local_service()
    return to_jsonable({
        "row_count": len(service.features_df),
        "max_row_index": max(0, len(service.features_df) - 1),
        "feature_count": len(service.feature_cols),
        "anomaly_label_count": len(service.anomaly_cols),
        "anomaly_threshold": service.anomaly_threshold,
        "obs_per_shift": service.obs_per_shift,
        "model_dir": str(service.model_dir),
        "processed_dir": str(service.processed_dir),
    })


@app.get("/api/v1/rows/{row_index}")
def row_by_index(row_index: int) -> dict[str, Any]:
    service = _local_service()
    try:
        return to_jsonable(service.row_by_index(row_index=row_index))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/v1/demo")
def get_demo_override() -> dict[str, Any]:
    return to_jsonable(_local_service().get_demo_override())


@app.post("/api/v1/demo/apply")
def apply_demo_override(request: DemoOverrideRequest) -> dict[str, Any]:
    service = _local_service()
    service.set_demo_override(request.row_index, request.row, meta=request.meta)
    return to_jsonable(service.get_demo_override())


@app.post("/api/v1/demo/clear")
def clear_demo_override() -> dict[str, Any]:
    service = _local_service()
    service.clear_demo_override()
    return {"enabled": False}


@app.get("/api/v1/topology")
def topology(
    row_index: int | None = Query(default=None, ge=0),
    strategy: str = Query(default="latest", pattern="^(latest|highest_risk)$"),
) -> list[dict[str, Any]]:
    return to_jsonable(_local_service().plant_topology(row_index=row_index, strategy=strategy))


@app.get("/api/v1/alarms/active")
def active_alarms(top_n: int = Query(default=20, ge=1, le=500)) -> list[dict[str, Any]]:
    return to_jsonable(_local_service().active_alarms(top_n=top_n))


@app.get("/api/v1/alarms/events")
def alarm_events(
    top_n: int = Query(default=25, ge=1, le=500),
    min_risk: str = Query(default="high", pattern="^(low|medium|high|critical)$"),
    gap: int = Query(default=8, ge=0, le=10000),
) -> list[dict[str, Any]]:
    return to_jsonable(_local_service().alarm_events(top_n=top_n, min_risk=min_risk, gap=gap))


@app.get("/api/v1/maintenance/queue")
def maintenance_queue(top_n: int = Query(default=8, ge=1, le=100)) -> list[dict[str, Any]]:
    return to_jsonable(_local_service().maintenance_queue(top_n=top_n))


@app.get("/api/v1/telemetry/window")
def telemetry_window(
    row_index: int | None = Query(default=None, ge=0),
    stand: int = Query(default=3, ge=1, le=5),
    window: int = Query(default=250, ge=1, le=5000),
    mode: str = Query(default="raw", pattern="^(raw|zscore|minmax|pct_change)$"),
) -> list[dict[str, Any]]:
    service = _local_service()
    if mode == "raw":
        frame = service.telemetry_window(row_index=row_index, stand=stand, window=window)
    else:
        frame = service.telemetry_window_normalized(
            row_index=row_index,
            stand=stand,
            window=window,
            mode=mode,
        )
    return to_jsonable(frame)


@app.get("/api/v1/telemetry/groups")
def telemetry_groups(
    row_index: int | None = Query(default=None, ge=0),
    stand: int = Query(default=3, ge=1, le=5),
    window: int = Query(default=250, ge=1, le=5000),
) -> dict[str, list[dict[str, Any]]]:
    groups = _local_service().telemetry_groups(row_index=row_index, stand=stand, window=window)
    return {name: to_jsonable(frame) for name, frame in groups.items()}


@app.get("/api/v1/model/metrics")
def model_metrics() -> dict[str, Any]:
    return to_jsonable(_local_service().metrics())


@app.get("/api/v1/model/drift")
def model_drift(top_n: int = Query(default=1000, ge=1, le=10000)) -> list[dict[str, Any]]:
    return to_jsonable(_local_service().drift_psi.head(top_n))


@app.get("/api/v1/model/feature-importance")
def model_feature_importance(top_n: int = Query(default=1000, ge=1, le=10000)) -> list[dict[str, Any]]:
    return to_jsonable(_local_service().feature_importance.head(top_n))
