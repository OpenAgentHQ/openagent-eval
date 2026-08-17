"""Custom exception hierarchy for OpenAgent Eval.

All exceptions inherit from OpenAgentEvalError for consistent error handling.
"""

from openagent_eval.exceptions.base import OpenAgentEvalError
from openagent_eval.exceptions.cli import CLIError, CommandError, ValidationError
from openagent_eval.exceptions.config import ConfigurationError
from openagent_eval.exceptions.corpus import (
    CorpusAuditError,
    CorpusError,
    CorpusNotFoundError,
    CorpusValidationError,
)
from openagent_eval.exceptions.dataset import (
    DatasetError,
    DatasetNotFoundError,
    DatasetValidationError,
    InvalidDatasetError,
)
from openagent_eval.exceptions.diagnosis import (
    BlameAttributionError,
    DiagnosisError,
    DiagnosisExecutionError,
)
from openagent_eval.exceptions.metric import (
    MetricError,
    MetricExecutionError,
    MetricNotFoundError,
    MetricTimeoutError,
)
from openagent_eval.exceptions.plugin import (
    PluginError,
    PluginLoadError,
    PluginNotFoundError,
)
from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderError,
    ProviderExecutionError,
    ProviderNotFoundError,
)
from openagent_eval.exceptions.synthesis import SynthesisError, SynthesisExecutionError

__all__ = [
    "OpenAgentEvalError",
    "ConfigurationError",
    "CorpusAuditError",
    "CorpusError",
    "CorpusNotFoundError",
    "CorpusValidationError",
    "DatasetError",
    "DatasetNotFoundError",
    "InvalidDatasetError",
    "DatasetValidationError",
    "MetricError",
    "MetricNotFoundError",
    "MetricExecutionError",
    "MetricTimeoutError",
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderConnectionError",
    "ProviderExecutionError",
    "PluginError",
    "PluginNotFoundError",
    "PluginLoadError",
    "CLIError",
    "CommandError",
    "ValidationError",
    "DiagnosisError",
    "DiagnosisExecutionError",
    "BlameAttributionError",
    "SynthesisError",
    "SynthesisExecutionError",
]
