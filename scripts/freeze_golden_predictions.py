from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.agentic.ml_service import MLModelService


STABLE_KEYS = [
    "alarm_id",
    "timestamp_index",
    "row_index",
    "is_alert",
    "anomaly_probability",
    "anomaly_threshold",
    "predicted_fault",
    "predicted_stand",
    "asset_name",
    "fault_confidence",
    "predicted_rul_band",
    "proxy_rul_observations",
    "proxy_rul_shifts",
    "trend_risk",
    "risk_score",
    "risk_level",
    "health_index",
    "evidence",
]


def _select_rows(service: MLModelService) -> list[tuple[str, int]]:
    hp = service.health_predictions.copy()
    if hp.empty or "risk_score" not in hp.columns or "timestamp_index" not in hp.columns:
        last = len(service.features_df) - 1
        return [("normal", 0), ("warning", max(0, last // 2)), ("critical", last)]

    hp["risk_score"] = pd.to_numeric(hp["risk_score"], errors="coerce")
    hp = hp.dropna(subset=["risk_score", "timestamp_index"])
    targets = {"normal": 15.0, "warning": 50.0, "critical": 95.0}
    selected: list[tuple[str, int]] = []

    for label, target in targets.items():
        if label == "normal":
            row = hp.sort_values("risk_score", ascending=True).iloc[0]
        elif label == "critical":
            row = hp.sort_values("risk_score", ascending=False).iloc[0]
        else:
            row = hp.iloc[(hp["risk_score"] - target).abs().argsort().iloc[0]]

        timestamp_index = int(row["timestamp_index"])
        matches = service.features_df.index[
            service.features_df["timestamp_index"].astype(int) == timestamp_index
        ].tolist()
        if not matches:
            raise RuntimeError(f"timestamp_index={timestamp_index} not found in feature parquet")
        selected.append((label, int(matches[0])))
    return selected


def _subset(result: dict[str, Any]) -> dict[str, Any]:
    return {key: result.get(key) for key in STABLE_KEYS}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="tests/golden/golden_predictions.json",
        help="Output JSON file.",
    )
    args = parser.parse_args()

    service = MLModelService().load()
    cases = []
    for label, row_index in _select_rows(service):
        result = service.predict_condition(row_index=row_index)
        cases.append(
            {
                "name": label,
                "row_index": row_index,
                "timestamp_index": result["timestamp_index"],
                "expected": _subset(result),
            }
        )

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feature_count": len(service.feature_cols),
        "row_count": len(service.features_df),
        "model_metadata_sha256": hashlib.sha256(
            Path(service.model_dir / "model_metadata.json").read_bytes()
        ).hexdigest(),
        "cases": cases,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(cases)} golden predictions to {output}")
    for case in cases:
        expected = case["expected"]
        print(
            f"  {case['name']}: row={case['row_index']} ts={case['timestamp_index']} "
            f"risk={expected['risk_score']} fault={expected['predicted_fault']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
