"""Framework error types with structured, AI-friendly detail."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ErrorPayload:
    """Structured error payload suitable for `--json` outputs."""

    code: str
    message: str
    hint: str | None = None
    context: Mapping[str, Any] | None = None


class ReneeError(Exception):
    """Base exception for Renee with structured payload."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        hint: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.payload = ErrorPayload(code=code, message=message, hint=hint, context=context)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.payload.code,
            "message": self.payload.message,
            "hint": self.payload.hint,
            "context": dict(self.payload.context or {}),
        }


class SchemaError(ReneeError):
    """Raised for schema registration/validation errors."""


class ValidationError(ReneeError):
    """Raised for generic validation failures."""

