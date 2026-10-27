from __future__ import annotations

import json
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

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

        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError:
            return MetricResult(
                score=0.0,
                reason="Invalid JSON schema",
                metadata={"valid": False, "json_parseable": True},
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
            and isinstance(schema, dict)
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
                failed_properties: set[str] = set()

                for name in applicable_properties:
                    if name not in data:
                        failed_properties.add(name)
                        continue

                    property_schema = properties[name]

                    if Draft202012Validator(property_schema).is_valid(data[name]):
                        valid_properties += 1
                    else:
                        failed_properties.add(name)

                # Any violation not already counted against a failed property
                # (e.g. additionalProperties, patternProperties, or a required
                # key outside top-level properties) counts as one extra failed
                # check, so the score stays below 1.0 without dropping to 0.0.
                def is_counted(error: Any) -> bool:
                    if error.absolute_path:
                        return error.absolute_path[0] in failed_properties
                    if error.validator == "required":
                        missing = [k for k in error.validator_value if k not in data]
                        return bool(missing) and set(missing) <= failed_properties
                    return False

                schema_level_failure = not all(is_counted(error) for error in errors)
                total_checks = len(applicable_properties) + int(schema_level_failure)
                score = valid_properties / total_checks

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
