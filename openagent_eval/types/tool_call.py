"""Provider-independent representation of a recorded agent tool call."""

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class ToolCall(BaseModel):
    """A tool name and its JSON arguments at one position in a trace."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    name: str = Field(min_length=1, pattern=r"\S")
    arguments: dict[str, JsonValue] = Field(default_factory=dict)
