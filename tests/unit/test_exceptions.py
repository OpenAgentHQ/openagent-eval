"""Tests for the exceptions module."""

from __future__ import annotations

from openagent_eval.exceptions import (
    CLIError,
    CommandError,
    ConfigurationError,
    DatasetError,
    DatasetNotFoundError,
    DatasetValidationError,
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
    ValidationError,
)


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
        error = InvalidDatasetError("Invalid format", format="json", line_number=10)
        assert error.format == "json"
        assert error.line_number == 10

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
        error = MetricNotFoundError("my_metric", available_metrics=["precision", "recall"])
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


class TestProviderError:
    """Tests for provider errors."""

    def test_basic_error(self) -> None:
        """Test basic provider error."""
        error = ProviderError("Invalid provider")
        assert str(error) == "Invalid provider"

    def test_not_found_error(self) -> None:
        """Test provider not found error."""
        error = ProviderNotFoundError("my_provider", available_providers=["openai", "gemini"])
        assert error.provider_name == "my_provider"
        assert error.available_providers == ["openai", "gemini"]

    def test_connection_error(self) -> None:
        """Test provider connection error."""
        original = ConnectionError("Connection failed")
        error = ProviderConnectionError("Failed to connect", original_error=original)
        assert error.original_error is original

    def test_execution_error(self) -> None:
        """Test provider execution error."""
        original = RuntimeError("Execution failed")
        error = ProviderExecutionError("Failed", original_error=original)
        assert error.original_error is original


class TestPluginError:
    """Tests for plugin errors."""

    def test_basic_error(self) -> None:
        """Test basic plugin error."""
        error = PluginError("Invalid plugin")
        assert str(error) == "Invalid plugin"

    def test_not_found_error(self) -> None:
        """Test plugin not found error."""
        error = PluginNotFoundError("my_plugin", available_plugins=["plugin1", "plugin2"])
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
        error = ValidationError("Invalid input", field="config_path", value="missing.yaml")
        assert error.field == "config_path"
        assert error.value == "missing.yaml"
