from typing import Any, Optional


class StructuredCallError(RuntimeError):
    """Raises when a structured-output request fails validation."""

    def __init__(
        self,
        message: str,
        *,
        raw_text: Optional[str] = None,
        parsed: Any = None,
        response_debug: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.raw_text = raw_text
        self.parsed = parsed
        self.response_debug = response_debug
