from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import tritonclient.http as httpclient


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


def infer(client: httpclient.InferenceServerClient, row_index: int) -> dict[str, Any]:
    payload = json.dumps({"row_index": row_index, "strategy": "latest"})
    tensor = httpclient.InferInput("REQUEST_JSON", [1], "BYTES")
    tensor.set_data_from_numpy(np.asarray([payload], dtype=object))
    result = client.infer(
        "vajra_predictor",
        inputs=[tensor],
        outputs=[httpclient.InferRequestedOutput("RESULT_JSON")],
    )
    raw = result.as_numpy("RESULT_JSON")[0]
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    parsed = json.loads(str(raw))
    if parsed.get("error"):
        raise RuntimeError(parsed)
    return parsed


def compare(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for key, exp in expected.items():
        got = actual.get(key)
        if key in NUMERIC_TOLERANCES and exp is not None:
            if not math.isclose(float(exp), float(got), abs_tol=NUMERIC_TOLERANCES[key]):
                failures.append(f"{key}: expected {exp}, got {got}")
        elif exp != got:
            failures.append(f"{key}: expected {exp!r}, got {got!r}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="127.0.0.1:8000")
    parser.add_argument("--golden", default="tests/golden/golden_predictions.json")
    args = parser.parse_args()

    golden = json.loads(Path(args.golden).read_text(encoding="utf-8"))
    client = httpclient.InferenceServerClient(url=args.url)
    all_failures: list[str] = []
    for case in golden["cases"]:
        actual = infer(client, int(case["row_index"]))
        failures = compare(case["expected"], actual)
        if failures:
            all_failures.extend([f"{case['name']}.{item}" for item in failures])
            print(f"FAIL {case['name']}")
        else:
            print(f"PASS {case['name']}")

    if all_failures:
        print("\nTriton parity failures:")
        for failure in all_failures:
            print(f"  - {failure}")
        return 1
    print("\nTriton output matches all frozen predictions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
