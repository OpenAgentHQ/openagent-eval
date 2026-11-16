from __future__ import annotations

import json
from typing import Any

from jsonschema import Draft202012Validator

from openagent_eval.metrics.base import BaseMetric, MetricResult


class SchemaConformance(BaseMetric):
    """Measure whether a generated JSON answer conforms to a JSON Schema."""

    name = "schema_conformance"
    description = "Measures JSON Schema conformance of a generated answer."

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate a generated answer against an expected JSON Schema."""
        answer = kwargs.get("answer", "")
        metadata = kwargs.get("metadata", {})

        schema = metadata.get("json_schema") if isinstance(metadata, dict) else None

        if schema is None:
            return MetricResult(
                score=0.0,
                reason="No JSON schema provided",
                metadata={"valid": False, "json_parseable": False},
            )

        try:
            data = json.loads(answer)
        except (json.JSONDecodeError, TypeError):
            return MetricResult(
                score=0.0,
                reason="Answer is not valid JSON",
                metadata={"valid": False, "json_parseable": False},
            )

        validator = Draft202012Validator(schema)
        errors = list(validator.iter_errors(data))

        if not errors:
            return MetricResult(
                score=1.0,
                reason="Answer conforms to JSON schema",
                metadata={
                    "valid": True,
                    "json_parseable": True,
                },
            )

        # For object schemas, provide deterministic top-level
        # field-level partial scoring.
        if (
            isinstance(data, dict)
            and schema.get("type") == "object"
            and isinstance(schema.get("properties"), dict)
        ):
            properties = schema["properties"]
            required = set(schema.get("required", []))

            applicable_properties = [
                name for name in properties if name in data or name in required
            ]

            if applicable_properties:
                valid_properties = 0

                for name in applicable_properties:
                    if name not in data:
                        continue

                    property_schema = properties[name]

                    if Draft202012Validator(property_schema).is_valid(data[name]):
                        valid_properties += 1

                score = valid_properties / len(applicable_properties)

                if score == 1.0 and errors:
                    score = 0.0

                return MetricResult(
                    score=score,
                    reason="Answer partially conforms to JSON schema",
                    metadata={
                        "valid": False,
                        "json_parseable": True,
                        "valid_properties": valid_properties,
                        "total_properties": len(applicable_properties),
                    },
                )

        return MetricResult(
            score=0.0,
            reason="Answer does not conform to JSON schema",
            metadata={
                "valid": False,
                "json_parseable": True,
            },
        )
