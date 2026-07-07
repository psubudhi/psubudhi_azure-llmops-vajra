from __future__ import annotations

import sys
from pathlib import Path


REQUIRED = [
    Path("tcm_modelling/models/model_metadata.json"),
    Path("tcm_modelling/models/anomaly_classifier.joblib"),
    Path("tcm_modelling/models/fault_multilabel_classifier.joblib"),
    Path("tcm_modelling/models/rul_urgency_classifier.joblib"),
    Path("tcm_modelling/models/proxy_rul_regressor.joblib"),
    Path("tcm_modelling/data/processed/tcm_features_dataset3.parquet"),
]

OPTIONAL = [
    Path("tcm_modelling/models/case_memory_preprocessor.joblib"),
    Path("tcm_modelling/models/case_memory_nearest_neighbors.joblib"),
]


def main() -> int:
    missing = [str(path) for path in REQUIRED if not path.exists()]
    print("Required artifacts:")
    for path in REQUIRED:
        print(f"  {'OK' if path.exists() else 'MISSING'}  {path}")
    print("Optional artifacts:")
    for path in OPTIONAL:
        print(f"  {'OK' if path.exists() else 'SKIP'}  {path}")
    if missing:
        print("\nRestore the missing files before running the baseline or API.")
        return 1
    print("\nAll mandatory artifacts are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
