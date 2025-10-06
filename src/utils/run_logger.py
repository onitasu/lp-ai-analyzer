import json
import os
import time
from typing import Any, Dict, Optional


class RunLogger:
    """Accumulates run metadata and persists it as JSON for each step."""

    def __init__(self, run_dir: str, url: Optional[str] = None):
        self.run_dir = run_dir
        self.log_path = os.path.join(run_dir, "run_log.json")
        self.data: Dict[str, Any] = {
            "url": url,
            "created_at": self._now(),
            "steps": []
        }
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if isinstance(existing, dict):
                    self.data.update(existing)
                    self.data.setdefault("steps", [])
            except Exception:
                # If the existing log is corrupted, start fresh but do not crash the app.
                pass
        self._persist()

    def set_context(self, **kwargs: Any) -> None:
        """Attach additional context fields to the top-level record."""
        self.data.update(kwargs)
        self._persist()

    def add_step(self, name: str, status: str, *, message: Optional[str] = None, detail: Optional[Dict[str, Any]] = None) -> None:
        entry: Dict[str, Any] = {
            "timestamp": self._now(),
            "step": name,
            "status": status
        }
        if message:
            entry["message"] = message
        if detail is not None:
            entry["detail"] = detail
        self.data.setdefault("steps", []).append(entry)
        self._persist()

    def _persist(self) -> None:
        os.makedirs(self.run_dir, exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _now() -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
