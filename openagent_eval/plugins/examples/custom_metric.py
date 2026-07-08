"""Example custom metric plugin.

This module demonstrates how to create a custom metric plugin
for OpenAgent Eval.
"""

from __future__ import annotations

from openagent_eval.metrics.base import BaseMetric, MetricResult


class WordCountMetric(BaseMetric):
    """A custom metric that counts words in the answer.

    This is a simple example metric that demonstrates how to create
    a custom metric plugin for OpenAgent Eval.
    """

    name = "word_count"
    description = "Counts the number of words in the answer"

    def evaluate(self, **kwargs) -> MetricResult:
        """Evaluate the word count metric.

        Args:
            **kwargs: Must contain 'answer' key with the text to count.

        Returns:
            MetricResult with word count score.
        """
        answer = kwargs.get("answer", "")
        
        if not answer:
            return MetricResult(
                score=0.0,
                reason="No answer provided",
                metadata={"word_count": 0}
            )
        
        # Count words
        words = answer.split()
        word_count = len(words)
        
        # Normalize score (assuming 100 words is a good length)
        # This is a simple normalization - you can customize this
        normalized_score = min(word_count / 100.0, 1.0)
        
        return MetricResult(
            score=normalized_score,
            reason=f"Answer contains {word_count} words",
            metadata={
                "word_count": word_count,
                "normalized_score": normalized_score,
            }
        )

    def validate_inputs(self, **kwargs) -> None:
        """Validate metric inputs.

        Args:
            **kwargs: Inputs to validate.

        Raises:
            ValueError: If 'answer' is not a string.
        """
        answer = kwargs.get("answer")
        if answer is not None and not isinstance(answer, str):
            raise ValueError(
                f"Answer must be a string, got {type(answer).__name__}"
            )