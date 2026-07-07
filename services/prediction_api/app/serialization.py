from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd


def to_jsonable(value: Any) -> Any:
    """Recursively convert pandas/numpy values into strict JSON-safe values."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        converted = float(value)
        return converted if math.isfinite(converted) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, pd.Series):
        return {str(k): to_jsonable(v) for k, v in value.to_dict().items()}
    if isinstance(value, pd.DataFrame):
        return [to_jsonable(row) for row in value.to_dict(orient="records")]
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    if hasattr(value, "item"):
        try:
            return to_jsonable(value.item())
        except Exception:
            pass
    return str(value)
