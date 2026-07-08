"""Example plugins for OpenAgent Eval.

This package contains example plugins that demonstrate how to create
custom metrics, providers, and other components.
"""

from openagent_eval.plugins.examples.custom_metric import WordCountMetric

__all__ = ["WordCountMetric"]