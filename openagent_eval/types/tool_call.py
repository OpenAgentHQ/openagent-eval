"""Provider-independent representation of a recorded agent tool call."""

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ToolCall(BaseModel):
    """A tool name and its JSON arguments at one position in a trace."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, pattern=r"\S")
    arguments: dict[str, Any] = Field(default_factory=dict)

    @field_validator("arguments")
    @classmethod
    def validate_arguments(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Use the same JSON representation for SDK and file-based traces."""
        try:
            normalized: dict[str, Any] = json.loads(json.dumps(value, allow_nan=False))
        except (TypeError, ValueError) as exc:
            raise ValueError("Tool arguments must contain JSON values") from exc
        return normalized
