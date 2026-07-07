from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any

import numpy as np
import triton_python_backend_utils as pb_utils


class TritonPythonModel:
    """Triton Python backend adapter around the unchanged Vajra MLModelService."""

    def initialize(self, args: dict[str, str]) -> None:
        app_root = Path(os.getenv("VAJRA_APP_ROOT", "/opt/vajra"))
        if str(app_root) not in sys.path:
            sys.path.insert(0, str(app_root))

        modelling_root = Path(os.getenv("TCM_MODELLING_ROOT", app_root / "tcm_modelling"))

        from src.agentic.ml_service import MLModelService

        self.service = MLModelService(modelling_root=modelling_root)
        self.service.load()

    def execute(self, requests: list[Any]) -> list[Any]:
        responses = []
        for request in requests:
            try:
                input_tensor = pb_utils.get_input_tensor_by_name(request, "REQUEST_JSON")
                raw = input_tensor.as_numpy().reshape(-1)[0]
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                payload = json.loads(str(raw))

                result = self.service.predict_condition(
                    row_index=payload.get("row_index"),
                    strategy=payload.get("strategy", "latest"),
                )
                body = json.dumps(_jsonable(result), ensure_ascii=False)
            except Exception as exc:
                body = json.dumps(
                    {
                        "error": f"{type(exc).__name__}: {exc}",
                        "traceback": traceback.format_exc(limit=8),
                    },
                    ensure_ascii=False,
                )

            output_tensor = pb_utils.Tensor(
                "RESULT_JSON",
                np.asarray([body], dtype=object),
            )
            responses.append(pb_utils.InferenceResponse(output_tensors=[output_tensor]))
        return responses

    def finalize(self) -> None:
        self.service = None


def _jsonable(value: Any) -> Any:
    import math
    from datetime import date, datetime

    import pandas as pd

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        converted = float(value)
        return converted if math.isfinite(converted) else None
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, pd.Series):
        return {str(k): _jsonable(v) for k, v in value.to_dict().items()}
    if isinstance(value, pd.DataFrame):
        return [_jsonable(row) for row in value.to_dict(orient="records")]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "item"):
        try:
            return _jsonable(value.item())
        except Exception:
            pass
    return str(value)
