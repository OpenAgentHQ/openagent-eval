"""Tests for the exceptions module."""

from __future__ import annotations

from openagent_eval.exceptions import (
    CLIError,
    CommandError,
    ConfigurationError,
    CorpusAuditError,
    CorpusError,
    CorpusValidationError,
    DatasetError,
    DatasetNotFoundError,
    DatasetValidationError,
    DiagnosisExecutionError,
    InvalidDatasetError,
    MetricError,
    MetricExecutionError,
    MetricNotFoundError,
    MetricTimeoutError,
    OpenAgentEvalError,
    PluginError,
    PluginLoadError,
    PluginNotFoundError,
    ProviderConnectionError,
    ProviderError,
    ProviderExecutionError,
    ProviderNotFoundError,
    SynthesisExecutionError,
    ValidationError,
)


class FalsyException(Exception):
    """Exception whose truthiness is false despite being an exception."""

    def __bool__(self) -> bool:
        return False


class TestOpenAgentEvalError:
    """Tests for the base exception class."""

    def test_basic_error(self) -> None:
        """Test basic error creation."""
        error = OpenAgentEvalError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}

    def test_error_with_details(self) -> None:
        """Test error with details."""
        error = OpenAgentEvalError("Test error", details={"key": "value"})
        assert "key=value" in str(error)
        assert error.details == {"key": "value"}

    def test_error_repr(self) -> None:
        """Test error repr."""
        error = OpenAgentEvalError("Test error")
        assert repr(error) == "OpenAgentEvalError(message='Test error', details={})"


class TestConfigurationError:
    """Tests for configuration errors."""

    def test_basic_error(self) -> None:
        """Test basic configuration error."""
        error = ConfigurationError("Invalid config")
        assert str(error) == "Invalid config"

    def test_error_with_path(self) -> None:
        """Test error with config path."""
        error = ConfigurationError("Invalid config", config_path="config.yaml")
        assert error.config_path == "config.yaml"
        assert "config_path=config.yaml" in str(error)

    def test_error_with_field(self) -> None:
        """Test error with field."""
        error = ConfigurationError("Invalid field", field="llm.provider")
        assert error.field == "llm.provider"
        assert "field=llm.provider" in str(error)


class TestDatasetError:
    """Tests for dataset errors."""

    def test_basic_error(self) -> None:
        """Test basic dataset error."""
        error = DatasetError("Invalid dataset")
        assert str(error) == "Invalid dataset"

    def test_not_found_error(self) -> None:
        """Test dataset not found error."""
        error = DatasetNotFoundError("data.json")
        assert error.dataset_path == "data.json"
        assert "Dataset not found: data.json" in str(error)

    def test_invalid_dataset_error(self) -> None:
        """Test invalid dataset error."""
        error = InvalidDatasetError(
            "Invalid format", data_format="json", line_number=10
        )
        assert error.data_format == "json"
        assert error.line_number == 10

    def test_invalid_dataset_error_preserves_zero_line_number(self) -> None:
        """Test that line_number=0 is retained in error details and str representation."""
        error = InvalidDatasetError("Invalid line", line_number=0)
        assert error.line_number == 0
        assert error.details["line_number"] == 0
        assert "line_number=0" in str(error)

    def test_invalid_dataset_error_omits_none_line_number(self) -> None:
        """Test that line_number=None is excluded from error details."""
        error = InvalidDatasetError("Invalid format", data_format="json")
        assert error.line_number is None
        assert "line_number" not in error.details
        assert "line_number" not in str(error)

    def test_validation_error(self) -> None:
        """Test dataset validation error."""
        error = DatasetValidationError(
            "Validation failed",
            validation_errors=["Missing field: question"],
        )
        assert error.validation_errors == ["Missing field: question"]


class TestMetricError:
    """Tests for metric errors."""

    def test_basic_error(self) -> None:
        """Test basic metric error."""
        error = MetricError("Invalid metric")
        assert str(error) == "Invalid metric"

    def test_not_found_error(self) -> None:
        """Test metric not found error."""
        error = MetricNotFoundError(
            "my_metric", available_metrics=["precision", "recall"]
        )
        assert error.metric_name == "my_metric"
        assert error.available_metrics == ["precision", "recall"]

    def test_execution_error(self) -> None:
        """Test metric execution error."""
        original = ValueError("Original error")
        error = MetricExecutionError("Failed", original_error=original)
        assert error.original_error is original

    def test_timeout_error(self) -> None:
        """Test metric timeout error."""
        error = MetricTimeoutError("Timed out", timeout_seconds=30.0)
        assert error.timeout_seconds == 30.0

    def test_timeout_error_preserves_zero_timeout(self) -> None:
        """Test that a zero timeout is retained in the error details."""
        error = MetricTimeoutError("Timed out immediately", timeout_seconds=0.0)
        assert error.timeout_seconds == 0.0
        assert error.details["timeout_seconds"] == 0.0
        assert "timeout_seconds=0.0" in str(error)

    def test_timeout_error_omits_none_timeout(self) -> None:
        """Test that timeout_seconds=None is excluded from error details."""
        error = MetricTimeoutError("Timed out")
        assert error.timeout_seconds is None
        assert "timeout_seconds" not in error.details
        assert "timeout_seconds" not in str(error)


class TestDiagnosisError:
    """Tests for diagnosis errors."""

    def test_execution_error_includes_step_in_details(self) -> None:
        """Test that the failed step is visible in error details."""
        error = DiagnosisExecutionError("Failed", step="blame_attribution")

        assert error.step == "blame_attribution"
        assert error.details["step"] == "blame_attribution"


class TestProviderError:
    """Tests for provider errors."""

    def test_basic_error(self) -> None:
        """Test basic provider error with standardized format."""
        error = ProviderError("Invalid provider")
        assert str(error) == "Provider Error: Invalid provider"
        assert error.error_type == "Provider Error"

    def test_error_with_provider_name(self) -> None:
        """Test provider error with provider name in standardized format."""
        error = ProviderError(
            "API key not found",
            provider_name="openai",
        )
        assert str(error) == "[openai] Provider Error: API key not found"

    def test_not_found_error(self) -> None:
        """Test provider not found error."""
        error = ProviderNotFoundError(
            "my_provider", available_providers=["openai", "gemini"]
        )
        assert error.provider_name == "my_provider"
        assert error.available_providers == ["openai", "gemini"]
        assert error.error_type == "Provider Not Found"
        expected = (
            "[my_provider] Provider Not Found: "
            "Provider not found: my_provider. Available providers: openai, gemini "
            "(available_providers=['openai', 'gemini'])"
        )
        assert str(error) == expected

    def test_connection_error(self) -> None:
        """Test provider connection error."""
        original = ConnectionError("Connection failed")
        error = ProviderConnectionError(
            "Failed to connect",
            provider_name="gemini",
            original_error=original,
        )
        assert error.original_error is original
        assert error.error_type == "Connection Error"
        assert (
            str(error)
            == "[gemini] Connection Error: Failed to connect (original_error=Connection failed)"
        )

    def test_execution_error(self) -> None:
        """Test provider execution error."""
        original = RuntimeError("Execution failed")
        error = ProviderExecutionError(
            "API call failed",
            provider_name="anthropic",
            original_error=original,
        )
        assert error.original_error is original
        assert error.error_type == "Execution Error"
        assert (
            str(error)
            == "[anthropic] Execution Error: API call failed (original_error=Execution failed)"
        )


class TestPluginError:
    """Tests for plugin errors."""

    def test_basic_error(self) -> None:
        """Test basic plugin error."""
        error = PluginError("Invalid plugin")
        assert str(error) == "Invalid plugin"

    def test_not_found_error(self) -> None:
        """Test plugin not found error."""
        error = PluginNotFoundError(
            "my_plugin", available_plugins=["plugin1", "plugin2"]
        )
        assert error.plugin_name == "my_plugin"
        assert error.available_plugins == ["plugin1", "plugin2"]

    def test_load_error(self) -> None:
        """Test plugin load error."""
        original = ImportError("Module not found")
        error = PluginLoadError("Failed to load", original_error=original)
        assert error.original_error is original


class TestCLIError:
    """Tests for CLI errors."""

    def test_basic_error(self) -> None:
        """Test basic CLI error."""
        error = CLIError("Invalid command")
        assert str(error) == "Invalid command"

    def test_command_error(self) -> None:
        """Test command error with exit code."""
        error = CommandError("Failed", exit_code=1)
        assert error.exit_code == 1

    def test_validation_error(self) -> None:
        """Test validation error."""
        error = ValidationError(
            "Invalid input", field="config_path", value="missing.yaml"
        )
        assert error.field == "config_path"
        assert error.value == "missing.yaml"

    def test_validation_error_preserves_empty_string_field_and_value(self) -> None:
        """Test that empty string field and value are retained in error details and str representation."""
        error = ValidationError("Validation failed", field="", value="")
        assert error.field == ""
        assert error.value == ""
        assert error.details["field"] == ""
        assert error.details["value"] == ""
        assert "field=" in str(error)
        assert "value=" in str(error)

    def test_validation_error_omits_none_field_and_value(self) -> None:
        """Test that field=None and value=None are excluded from error details."""
        error = ValidationError("Validation failed")
        assert error.field is None
        assert error.value is None
        assert "field" not in error.details
        assert "value" not in error.details
        assert "field" not in str(error)
        assert "value" not in str(error)


class TestFalsyDetailRecording:
    """Explicitly-supplied falsy values (not None) must be recorded in .details.

    Guards must distinguish "not supplied" (None) from a falsy value such as
    "", 0, False or []. Only None may be dropped from .details.
    """

    # --- config.py ---

    def test_configuration_error_preserves_empty_config_path(self) -> None:
        error = ConfigurationError("Invalid config", config_path="")
        assert "config_path" in error.details

    def test_configuration_error_preserves_empty_field(self) -> None:
        error = ConfigurationError("Invalid config", field="")
        assert "field" in error.details

    def test_configuration_error_omits_none_parameters(self) -> None:
        error = ConfigurationError("Invalid config")
        assert "config_path" not in error.details
        assert "field" not in error.details

    # --- cli.py ---

    def test_cli_error_preserves_empty_command(self) -> None:
        error = CLIError("Invalid command", command="")
        assert "command" in error.details

    def test_cli_error_omits_none_command(self) -> None:
        error = CLIError("Invalid command")
        assert "command" not in error.details

    # --- corpus.py ---

    def test_corpus_error_preserves_empty_corpus_path(self) -> None:
        error = CorpusError("Corpus error", corpus_path="")
        assert "corpus_path" in error.details

    def test_corpus_error_omits_none_corpus_path(self) -> None:
        error = CorpusError("Corpus error")
        assert "corpus_path" not in error.details

    def test_corpus_validation_error_preserves_empty_validation_errors(self) -> None:
        error = CorpusValidationError("Validation failed", validation_errors=[])
        assert "validation_errors" in error.details

    def test_corpus_validation_error_omits_none_validation_errors(self) -> None:
        error = CorpusValidationError("Validation failed")
        assert "validation_errors" not in error.details

    def test_corpus_audit_error_preserves_empty_analyzer_name(self) -> None:
        error = CorpusAuditError("Audit failed", analyzer_name="")
        assert "analyzer_name" in error.details

    def test_corpus_audit_error_records_original_error(self) -> None:
        error = CorpusAuditError("Audit failed", original_error=ValueError("boom"))
        assert "original_error" in error.details

    def test_corpus_audit_error_preserves_falsy_original_error(self) -> None:
        original_error = FalsyException("boom")
        error = CorpusAuditError("Audit failed", original_error=original_error)
        assert "original_error" in error.details
        assert error.original_error is original_error

    def test_corpus_audit_error_omits_none_parameters(self) -> None:
        error = CorpusAuditError("Audit failed")
        assert "analyzer_name" not in error.details
        assert "original_error" not in error.details

    # --- dataset.py ---

    def test_dataset_error_preserves_empty_dataset_path(self) -> None:
        error = DatasetError("Dataset error", dataset_path="")
        assert "dataset_path" in error.details

    def test_dataset_error_omits_none_dataset_path(self) -> None:
        error = DatasetError("Dataset error")
        assert "dataset_path" not in error.details

    def test_invalid_dataset_error_preserves_empty_data_format(self) -> None:
        error = InvalidDatasetError("Invalid format", data_format="")
        assert "format" in error.details

    def test_invalid_dataset_error_omits_none_data_format(self) -> None:
        error = InvalidDatasetError("Invalid format")
        assert "format" not in error.details

    def test_dataset_validation_error_preserves_empty_validation_errors(self) -> None:
        error = DatasetValidationError("Validation failed", validation_errors=[])
        assert "validation_errors" in error.details

    def test_dataset_validation_error_omits_none_validation_errors(self) -> None:
        error = DatasetValidationError("Validation failed")
        assert "validation_errors" not in error.details

    # --- metric.py ---

    def test_metric_error_preserves_empty_metric_name(self) -> None:
        error = MetricError("Metric error", metric_name="")
        assert "metric_name" in error.details

    def test_metric_error_omits_none_metric_name(self) -> None:
        error = MetricError("Metric error")
        assert "metric_name" not in error.details

    def test_metric_not_found_error_preserves_empty_available_metrics(self) -> None:
        error = MetricNotFoundError("my_metric", available_metrics=[])
        assert "available_metrics" in error.details

    def test_metric_not_found_error_omits_none_available_metrics(self) -> None:
        error = MetricNotFoundError("my_metric")
        assert "available_metrics" not in error.details

    def test_metric_execution_error_records_original_error(self) -> None:
        error = MetricExecutionError("Failed", original_error=ValueError("boom"))
        assert "original_error" in error.details

    def test_metric_execution_error_preserves_falsy_original_error(self) -> None:
        original_error = FalsyException("boom")
        error = MetricExecutionError("Failed", original_error=original_error)
        assert "original_error" in error.details
        assert error.original_error is original_error

    def test_metric_execution_error_omits_none_original_error(self) -> None:
        error = MetricExecutionError("Failed")
        assert "original_error" not in error.details

    # --- plugin.py ---

    def test_plugin_error_preserves_empty_plugin_name(self) -> None:
        error = PluginError("Plugin error", plugin_name="")
        assert "plugin_name" in error.details

    def test_plugin_error_omits_none_plugin_name(self) -> None:
        error = PluginError("Plugin error")
        assert "plugin_name" not in error.details

    def test_plugin_not_found_error_preserves_empty_available_plugins(self) -> None:
        error = PluginNotFoundError("my_plugin", available_plugins=[])
        assert "available_plugins" in error.details

    def test_plugin_not_found_error_omits_none_available_plugins(self) -> None:
        error = PluginNotFoundError("my_plugin")
        assert "available_plugins" not in error.details

    def test_plugin_load_error_records_original_error(self) -> None:
        error = PluginLoadError("Failed to load", original_error=ImportError("boom"))
        assert "original_error" in error.details

    def test_plugin_load_error_preserves_falsy_original_error(self) -> None:
        original_error = FalsyException("boom")
        error = PluginLoadError("Failed to load", original_error=original_error)
        assert "original_error" in error.details
        assert error.original_error is original_error

    def test_plugin_load_error_omits_none_original_error(self) -> None:
        error = PluginLoadError("Failed to load")
        assert "original_error" not in error.details

    # --- provider.py ---

    def test_provider_error_preserves_empty_provider_name(self) -> None:
        error = ProviderError("Provider error", provider_name="")
        assert "provider_name" in error.details

    def test_provider_error_omits_none_provider_name(self) -> None:
        error = ProviderError("Provider error")
        assert "provider_name" not in error.details

    def test_provider_not_found_error_preserves_empty_available_providers(self) -> None:
        error = ProviderNotFoundError("my_provider", available_providers=[])
        assert "available_providers" in error.details

    def test_provider_not_found_error_omits_none_available_providers(self) -> None:
        error = ProviderNotFoundError("my_provider")
        assert "available_providers" not in error.details

    def test_provider_connection_error_records_original_error(self) -> None:
        error = ProviderConnectionError(
            "Failed to connect", original_error=ConnectionError("boom")
        )
        assert "original_error" in error.details

    def test_provider_connection_error_preserves_falsy_original_error(self) -> None:
        original_error = FalsyException("boom")
        error = ProviderConnectionError(
            "Failed to connect", original_error=original_error
        )
        assert "original_error" in error.details
        assert error.original_error is original_error

    def test_provider_connection_error_omits_none_original_error(self) -> None:
        error = ProviderConnectionError("Failed to connect")
        assert "original_error" not in error.details

    def test_provider_execution_error_records_original_error(self) -> None:
        error = ProviderExecutionError(
            "API call failed", original_error=RuntimeError("boom")
        )
        assert "original_error" in error.details

    def test_provider_execution_error_preserves_falsy_original_error(self) -> None:
        original_error = FalsyException("boom")
        error = ProviderExecutionError("API call failed", original_error=original_error)
        assert "original_error" in error.details
        assert error.original_error is original_error

    def test_provider_execution_error_omits_none_original_error(self) -> None:
        error = ProviderExecutionError("API call failed")
        assert "original_error" not in error.details

    # --- synthesis.py ---

    def test_synthesis_execution_error_records_original_error(self) -> None:
        error = SynthesisExecutionError(
            "Synthesis failed", original_error=RuntimeError("boom")
        )
        assert "original_error" in error.details

    def test_synthesis_execution_error_preserves_falsy_original_error(self) -> None:
        original_error = FalsyException("boom")
        error = SynthesisExecutionError(
            "Synthesis failed", original_error=original_error
        )
        assert "original_error" in error.details
        assert error.original_error is original_error

    def test_synthesis_execution_error_omits_none_original_error(self) -> None:
        error = SynthesisExecutionError("Synthesis failed")
        assert "original_error" not in error.details
