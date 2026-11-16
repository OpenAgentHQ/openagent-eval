"""Plugin/component registry for OpenAgent Eval."""

from __future__ import annotations

from typing import Any

from openagent_eval.exceptions import PluginNotFoundError


class Registry:
    """Central registry for metrics, providers, and other components.

    This class manages the discovery and registration of plugins,
    metrics, providers, and other extensible components.
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._metrics: dict[str, type[Any]] = {}
        self._providers: dict[str, type[Any]] = {}
        self._retrievers: dict[str, type[Any]] = {}
        self._dataset_loaders: dict[str, type[Any]] = {}
        self._report_generators: dict[str, type[Any]] = {}

    def register_metric(self, name: str, metric_class: type[Any]) -> None:
        """Register a metric class.

        Args:
            name: The metric name.
            metric_class: The metric class to register.
        """
        self._metrics[name] = metric_class

    def register_provider(self, name: str, provider_class: type[Any]) -> None:
        """Register a provider class.

        Args:
            name: The provider name.
            provider_class: The provider class to register.
        """
        self._providers[name] = provider_class

    def register_retriever(self, name: str, retriever_class: type[Any]) -> None:
        """Register a retriever class.

        Args:
            name: The retriever name.
            retriever_class: The retriever class to register.
        """
        self._retrievers[name] = retriever_class

    def register_dataset_loader(self, name: str, loader_class: type[Any]) -> None:
        """Register a dataset loader class.

        Args:
            name: The loader name.
            loader_class: The loader class to register.
        """
        self._dataset_loaders[name] = loader_class

    def register_report_generator(self, name: str, generator_class: type[Any]) -> None:
        """Register a report generator class.

        Args:
            name: The generator name.
            generator_class: The generator class to register.
        """
        self._report_generators[name] = generator_class

    def get_metric(self, name: str) -> type[Any]:
        """Get a registered metric class.

        Args:
            name: The metric name.

        Returns:
            The metric class.

        Raises:
            PluginNotFoundError: If the metric is not registered.
        """
        if name not in self._metrics:
            available = list(self._metrics.keys())
            raise PluginNotFoundError(
                plugin_name=name,
                details={"available_metrics": available},
            )
        return self._metrics[name]

    def get_provider(self, name: str) -> type[Any]:
        """Get a registered provider class.

        Args:
            name: The provider name.

        Returns:
            The provider class.

        Raises:
            PluginNotFoundError: If the provider is not registered.
        """
        if name not in self._providers:
            available = list(self._providers.keys())
            raise PluginNotFoundError(
                plugin_name=name,
                details={"available_providers": available},
            )
        return self._providers[name]

    def get_retriever(self, name: str) -> type[Any]:
        """Get a registered retriever class.

        Args:
            name: The retriever name.

        Returns:
            The retriever class.

        Raises:
            PluginNotFoundError: If the retriever is not registered.
        """
        if name not in self._retrievers:
            available = list(self._retrievers.keys())
            raise PluginNotFoundError(
                plugin_name=name,
                details={"available_retrievers": available},
            )
        return self._retrievers[name]

    def list_metrics(self) -> list[str]:
        """List all registered metric names.

        Returns:
            List of metric names.
        """
        return list(self._metrics.keys())

    def list_providers(self) -> list[str]:
        """List all registered provider names.

        Returns:
            List of provider names.
        """
        return list(self._providers.keys())

    def list_retrievers(self) -> list[str]:
        """List all registered retriever names.

        Returns:
            List of retriever names.
        """
        return list(self._retrievers.keys())
