from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import httpx


NUMERIC_TOLERANCES = {
    "anomaly_probability": 1e-4,
    "anomaly_threshold": 1e-4,
    "fault_confidence": 1e-4,
    "proxy_rul_observations": 1e-2,
    "proxy_rul_shifts": 1e-2,
    "trend_risk": 1e-4,
    "risk_score": 1e-2,
    "health_index": 1e-2,
}


def _compare(expected: dict[str, Any], actual: dict[str, Any], prefix: str = "") -> list[str]:
    errors: list[str] = []
    for key, exp in expected.items():
        path = f"{prefix}.{key}" if prefix else key
        if key not in actual:
            errors.append(f"{path}: missing from actual response")
            continue
        got = actual[key]
        if key in NUMERIC_TOLERANCES and exp is not None:
            try:
                if not math.isclose(float(exp), float(got), abs_tol=NUMERIC_TOLERANCES[key]):
                    errors.append(f"{path}: expected {exp}, got {got}")
            except Exception:
                errors.append(f"{path}: expected numeric {exp}, got {got!r}")
        elif exp != got:
            errors.append(f"{path}: expected {exp!r}, got {got!r}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--golden", default="tests/golden/golden_predictions.json")
    args = parser.parse_args()

    golden = json.loads(Path(args.golden).read_text(encoding="utf-8"))
    failures: list[str] = []
    with httpx.Client(base_url=args.base_url, timeout=120) as client:
        ready = client.get("/health/ready")
        ready.raise_for_status()
        for case in golden["cases"]:
            response = client.post(
                "/api/v1/predictions",
                json={"row_index": case["row_index"], "strategy": "latest"},
            )
            response.raise_for_status()
            errors = _compare(case["expected"], response.json(), prefix=case["name"])
            if errors:
                failures.extend(errors)
                print(f"FAIL {case['name']}")
            else:
                print(f"PASS {case['name']}")

    if failures:
        print("\nParity failures:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("\nAll API predictions match the frozen baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
