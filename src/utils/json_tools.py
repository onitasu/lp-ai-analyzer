"""Utilities for converting arbitrary SDK objects into JSON-serializable values."""
from __future__ import annotations

from typing import Any


def make_json_safe(value: Any) -> Any:
    """Recursively convert SDK objects into JSON-serializable primitives.

    Handles common patterns such as Pydantic/BaseModel, dataclasses, and
    objects exposing to_dict()/model_dump(). Falls back to string conversion
    when no structured representation is available.
    """

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(v) for v in value]

    if isinstance(value, dict):
        return {str(k): make_json_safe(v) for k, v in value.items()}

    for attr in ("model_dump", "dict", "to_dict", "as_dict"):
        method = getattr(value, attr, None)
        if callable(method):
            try:
                return make_json_safe(method())
            except Exception:
                continue

    if hasattr(value, "__dict__"):
        try:
            return make_json_safe(vars(value))
        except Exception:
            pass

    return str(value)
